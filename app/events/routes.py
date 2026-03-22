from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.events.nlp import NLPService, ParseResult
from app.events.ocr import OCRService
from app.events.repository import EventRepository
from app.events.schemas import CategoryCreate, CategoryResponse, EventCreate, EventResponse, EventUpdate
from app.events.service import EventService
from app.i18n import resolve_locale, translate
from app.sync.service import GoogleSyncService
from app.users.repository import UserRepository

router = APIRouter(prefix="/api/events", tags=["events"])


class ParseEventRequest(BaseModel):
    """Request to parse natural language event text."""

    text: str
    context_date: Optional[str] = None  # ISO date, defaults to today


class ParseEventResponse(BaseModel):
    """Response from parsing natural language event text."""

    title: str
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    timezone: str
    confidence_date: float
    confidence_title: float
    recurrence: Optional[dict] = None
    errors: list[str]
    raw_text: str
    ambiguous: bool = False
    year_candidates: list[int] = []


class OCRParseResponse(BaseModel):
    """Response from OCR-assisted parse."""

    title: str
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    timezone: str
    confidence_title: float
    confidence_date: float
    confidence_raw: float
    raw_text: str
    errors: list[str]


def _service(db) -> EventService:
    return EventService(EventRepository(db))


def _msg(user_locale: str, key: str, **kwargs) -> str:
    return translate(key, user_locale, **kwargs)


def _resolve_timezone(user, db) -> str:
    """Resolve timezone from authenticated user context with safe UTC fallback."""
    user_timezone = getattr(user, "timezone", None)
    if isinstance(user_timezone, str) and user_timezone.strip():
        return user_timezone.strip()

    calendar_id = getattr(user, "calendar_id", None)
    if calendar_id:
        try:
            calendar = UserRepository(db).get_calendar_by_id(calendar_id)
            if calendar and calendar.timezone:
                return calendar.timezone
        except Exception:
            pass

    return "UTC"


@router.post("/parse", response_model=ParseEventResponse)
async def parse_event(payload: ParseEventRequest, request: Request, user=Depends(get_current_user), db=Depends(get_db)):
    """Parse natural language text into structured event data."""
    # Determine context date
    context_date = None
    user_locale = resolve_locale(request)
    if payload.context_date:
        try:
            context_date = datetime.fromisoformat(payload.context_date)
        except ValueError:
            raise HTTPException(status_code=400, detail=_msg(user_locale, "events.invalid_context_date")) from None
    
    timezone = _resolve_timezone(user, db)
    
    # Parse the text
    nlp = NLPService()
    result = nlp.parse(payload.text, timezone, context_date, locale=user_locale)

    # Return as response model
    return ParseEventResponse(
        title=result.title,
        start_at=result.start_at,
        end_at=result.end_at,
        timezone=timezone,
        confidence_date=result.confidence_date,
        confidence_title=result.confidence_title,
        recurrence=result.recurrence,
        errors=result.errors,
        raw_text=result.raw_text,
        ambiguous=result.ambiguous,
        year_candidates=result.year_candidates,
    )


@router.post("/ocr-parse", response_model=OCRParseResponse)
async def parse_event_from_image(
    request: Request,
    image: UploadFile = File(...),
    context_date: Optional[str] = None,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Parse event details from uploaded image text using OCR + NLP."""
    user_locale = resolve_locale(request)
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail=_msg(user_locale, "events.upload_empty"))

    parsed_context = None
    if context_date:
        try:
            parsed_context = datetime.fromisoformat(context_date)
        except ValueError:
            raise HTTPException(status_code=400, detail=_msg(user_locale, "events.invalid_context_date")) from None

    timezone = _resolve_timezone(user, db)
    result = OCRService().parse_image(image_bytes, timezone, parsed_context, locale=user_locale)

    return OCRParseResponse(
        title=result.title,
        start_at=result.start_at,
        end_at=result.end_at,
        timezone=result.timezone,
        confidence_title=result.confidence_title,
        confidence_date=result.confidence_date,
        confidence_raw=result.confidence_raw,
        raw_text=result.raw_text,
        errors=result.errors,
    )


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(user=Depends(get_current_user), db=Depends(get_db)):
    service = _service(db)
    categories = service.list_categories(user.calendar_id)
    return categories


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryCreate, user=Depends(get_current_user), db=Depends(get_db)):
    service = _service(db)
    category = service.create_category(user.calendar_id, payload)
    return category


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(payload: EventCreate, user=Depends(get_current_user), db=Depends(get_db)):
    service = _service(db)
    try:
        event = service.create_event(user.calendar_id, user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        GoogleSyncService(db).sync_event_for_household(event, deleted=False)
    except Exception:
        pass
    return event


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(event_id: str, payload: EventUpdate, user=Depends(get_current_user), db=Depends(get_db)):
    service = _service(db)
    try:
        event = service.update_event(event_id, user.calendar_id, user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        GoogleSyncService(db).sync_event_for_household(event, deleted=False)
    except Exception:
        pass
    return event


@router.delete("/{event_id}")
async def delete_event(event_id: str, request: Request, user=Depends(get_current_user), db=Depends(get_db)):
    service = _service(db)
    try:
        event = service.delete_event(event_id, user.calendar_id, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        GoogleSyncService(db).sync_event_for_household(event, deleted=True)
    except Exception:
        pass
    return {"message": _msg(resolve_locale(request), "events.deleted")}


@router.get("/day", response_model=list[EventResponse])
async def list_day(
    year: int = Query(...),
    month: int = Query(...),
    day: int = Query(...),
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = _service(db)
    return service.list_day(user.calendar_id, year, month, day, requesting_user_id=user.id)


@router.get("/month", response_model=list[EventResponse])
async def list_month(
    year: int = Query(...),
    month: int = Query(...),
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = _service(db)
    return service.list_month(user.calendar_id, year, month, requesting_user_id=user.id)
