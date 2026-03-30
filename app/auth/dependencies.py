from datetime import datetime
import uuid
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Response
from pydantic import BaseModel

from app.auth.supabase_auth import (
    decode_legacy_session_token,
    fetch_supabase_user,
    refresh_supabase_access_token,
)
from app.database.database import get_db
from app.database.models import User
from app.users.repository import UserRepository
from app.users.service import UserService
from config import Settings


class AuthenticatedUser(BaseModel):
    id: str
    email: str
    name: str
    google_id: str | None = None
    calendar_id: str | None = None
    last_login: datetime | None = None


async def get_current_user(
    session: Optional[str] = Cookie(None),
    supabase_refresh: Optional[str] = Cookie(None),
    response: Response = None,
    db=Depends(get_db),
) -> User | AuthenticatedUser:
    repo = UserRepository(db)
    settings = Settings()
    _secure = settings.ENVIRONMENT != "development"

    if not session:
        if not supabase_refresh:
            raise HTTPException(status_code=401, detail="Not authenticated")

        refreshed = await refresh_supabase_access_token(supabase_refresh)
        if not refreshed:
            raise HTTPException(status_code=401, detail="Not authenticated")

        session = refreshed.get("access_token")
        new_refresh = refreshed.get("refresh_token") or supabase_refresh
        if response and session:
            response.set_cookie("session", session, httponly=True, secure=_secure, samesite="lax", max_age=settings.SESSION_COOKIE_MAX_AGE)
            response.set_cookie("supabase_refresh", new_refresh, httponly=True, secure=_secure, samesite="lax", max_age=settings.REFRESH_COOKIE_MAX_AGE)

    legacy_payload = decode_legacy_session_token(session)
    if legacy_payload:
        user_id = legacy_payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid session")

        user = repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user

    supabase_user = await fetch_supabase_user(session)
    if not supabase_user and supabase_refresh:
        refreshed = await refresh_supabase_access_token(supabase_refresh)
        if refreshed:
            session = refreshed.get("access_token")
            new_refresh = refreshed.get("refresh_token") or supabase_refresh
            if response and session:
                response.set_cookie("session", session, httponly=True, secure=_secure, samesite="lax", max_age=settings.SESSION_COOKIE_MAX_AGE)
                response.set_cookie("supabase_refresh", new_refresh, httponly=True, secure=_secure, samesite="lax", max_age=settings.REFRESH_COOKIE_MAX_AGE)
            supabase_user = await fetch_supabase_user(session)

    if not supabase_user:
        raise HTTPException(status_code=401, detail="Invalid session")

    email = (supabase_user.get("email") or "").lower()
    if not email:
        raise HTTPException(status_code=401, detail="Supabase user has no email")

    metadata = supabase_user.get("user_metadata") or {}
    full_name = metadata.get("full_name") or metadata.get("name") or email
    external_id = supabase_user.get("id") or ""

    try:
        user = repo.get_user_by_email(email, auth_token=session)
        if not user:
            new_user_id = str(uuid.uuid4())
            user = repo.create_user(
                {
                    "id": new_user_id,
                    "email": email,
                    "name": full_name,
                    "google_id": external_id,
                    "last_login": datetime.utcnow().isoformat(),
                },
                auth_token=session,
            )
            calendar = repo.create_calendar(
                {
                    "id": str(uuid.uuid4()),
                    "name": f"{full_name}'s Calendar",
                    "owner_user_id": new_user_id,
                },
                auth_token=session,
            )
            user = repo.update_user(user.id, {"calendar_id": calendar.id}, auth_token=session) or user
            # Accept pending invitations for brand-new users.
            try:
                service = UserService(db)
                service.accept_household_invitation(user.id)
            except Exception:
                pass
        else:
            # Only update last_login if stale (>5 min) to avoid a PATCH + re-fetch on every request.
            needs_update = False
            update_payload = {}
            if not user.calendar_id:
                calendar = repo.create_calendar(
                    {
                        "id": str(uuid.uuid4()),
                        "name": f"{full_name or email}'s Calendar",
                        "owner_user_id": user.id,
                    },
                    auth_token=session,
                )
                update_payload["calendar_id"] = calendar.id
                needs_update = True
            now = datetime.utcnow()
            last = getattr(user, "last_login", None)
            if not last or (now - last).total_seconds() > 300:
                update_payload["last_login"] = now.isoformat()
                update_payload["name"] = full_name or user.name
                update_payload["google_id"] = user.google_id or external_id
                needs_update = True
            if needs_update:
                user = repo.update_user(user.id, update_payload, auth_token=session) or user
        return user
    except Exception:
        # Allow auth to continue when SQL connectivity is temporarily unavailable.
        return AuthenticatedUser(
            id=external_id or email,
            email=email,
            name=full_name,
            google_id=external_id or None,
            calendar_id=None,
            last_login=datetime.utcnow(),
        )


async def get_current_user_optional(
    session: Optional[str] = Cookie(None),
    supabase_refresh: Optional[str] = Cookie(None),
    response: Response = None,
    db=Depends(get_db),
) -> User | AuthenticatedUser | None:
    """Same as get_current_user but returns None instead of raising 401."""
    try:
        return await get_current_user(session, supabase_refresh, response, db)
    except Exception:
        return None
