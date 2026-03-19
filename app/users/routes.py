from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr

from app.auth.supabase_auth import (
    decode_legacy_session_token,
    fetch_supabase_user,
    refresh_supabase_access_token,
)
from app.auth.dependencies import get_current_user
from app.database.supabase_store import SupabaseStoreError
from app.database.database import get_db
from app.i18n import resolve_locale, translate
from app.users.service import UserService

router = APIRouter(prefix="/api/users", tags=["users"])


def _msg(request: Request, key: str, **kwargs) -> str:
    return translate(key, resolve_locale(request), **kwargs)


class InviteRequest(BaseModel):
    email: EmailStr


class InvitationResponse(BaseModel):
    message: str
    invited_email: str


@router.get("/me")
async def get_current_user_info(user=Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "calendar_id": user.calendar_id,
        "last_login": user.last_login,
    }


@router.get("/household")
async def get_household_info(user=Depends(get_current_user), db=Depends(get_db)):
    service = UserService(db)
    info = service.get_household_info(user.id)

    return {
        "calendar_id": info["calendar"].id if info["calendar"] else None,
        "calendar_name": info["calendar"].name if info["calendar"] else None,
        "member_count": info["member_count"],
        "members": [{"id": m.id, "email": m.email, "name": m.name} for m in info["members"]],
    }


@router.post("/invite", response_model=InvitationResponse)
async def invite_household_member(
    http_request: Request,
    request: InviteRequest,
    user=Depends(get_current_user),
    db=Depends(get_db),
    session: Optional[str] = Cookie(None),
    supabase_refresh: Optional[str] = Cookie(None),
):
    if request.email.lower() == user.email.lower():
        raise HTTPException(status_code=400, detail=_msg(http_request, "users.cannot_invite_self"))

    db_auth_token = session
    if session and decode_legacy_session_token(session):
        db_auth_token = None

    if db_auth_token:
        supabase_profile = await fetch_supabase_user(db_auth_token)
        if not supabase_profile:
            db_auth_token = None

    if not db_auth_token and supabase_refresh:
        refreshed = await refresh_supabase_access_token(supabase_refresh)
        if refreshed:
            db_auth_token = refreshed.get("access_token")

    if not db_auth_token:
        raise HTTPException(
            status_code=401,
            detail=_msg(http_request, "users.supabase_required"),
        )

    service = UserService(db)
    try:
        invitation = service.invite_user(
            user.id,
            request.email,
            inviter_email=user.email,
            inviter_name=user.name,
            inviter_external_id=getattr(user, "google_id", None) or user.id,
            auth_token=db_auth_token,
        )
        return InvitationResponse(
            message=_msg(http_request, "users.invitation_sent", email=request.email),
            invited_email=invitation.invited_email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SupabaseStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/accept-invitation")
async def accept_invitation(request: Request, user=Depends(get_current_user), db=Depends(get_db)):
    service = UserService(db)
    result = service.accept_household_invitation(user.id)

    if result:
        return {"message": _msg(request, "users.invitation_accepted"), "calendar_id": result.calendar_id}
    return {"message": _msg(request, "users.no_pending_invitations")}
