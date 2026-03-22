import calendar
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.events.repository import EventRepository
from app.events.service import EventService
from app.i18n import inject_template_i18n

router = APIRouter(prefix="/calendar", tags=["calendar"])
templates = Jinja2Templates(directory="app/templates")


def _service(db) -> EventService:
    return EventService(EventRepository(db))


@router.get("/month", response_class=HTMLResponse)
async def month_grid(
    request: Request,
    year: int = Query(...),
    month: int = Query(...),
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = _service(db)
    events = service.list_month_expanded(user.calendar_id, year, month, requesting_user_id=user.id)
    categories = service.list_categories(user.calendar_id)
    category_map = {cat.id: cat for cat in categories}

    days = calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)

    event_map: dict[str, list] = {}
    for event in events:
        key = event.start_at.date().isoformat()
        event_map.setdefault(key, []).append(event)

    prev_dt = (datetime(year, month, 1) - timedelta(days=1)).replace(day=1)
    next_dt = (datetime(year, month, 28) + timedelta(days=4)).replace(day=1)

    context = inject_template_i18n(
        request,
        {
            "request": request,
            "weeks": days,
            "event_map": event_map,
            "category_map": category_map,
            "display_year": year,
            "display_month": month,
            "display_month_name": calendar.month_name[month],
            "prev_year": prev_dt.year,
            "prev_month": prev_dt.month,
            "next_year": next_dt.year,
            "next_month": next_dt.month,
            "today": datetime.utcnow().date(),
        },
    )

    return templates.TemplateResponse(request=request, name="partials/month_grid.html", context=context)


@router.get("/day", response_class=HTMLResponse)
async def day_events(
    request: Request,
    year: int = Query(...),
    month: int = Query(...),
    day: int = Query(...),
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = _service(db)
    events = service.list_day_expanded(user.calendar_id, year, month, day, requesting_user_id=user.id)
    categories = service.list_categories(user.calendar_id)
    category_map = {cat.id: cat for cat in categories}

    context = inject_template_i18n(
        request,
        {
            "request": request,
            "events": events,
            "category_map": category_map,
            "date_label": f"{year:04d}-{month:02d}-{day:02d}",
        },
    )

    return templates.TemplateResponse(request=request, name="partials/day_events.html", context=context)
