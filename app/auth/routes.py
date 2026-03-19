from datetime import datetime, timedelta
import json
import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, EmailStr

from app.auth.oauth import exchange_code_for_token, get_authorization_url
from app.auth.supabase_auth import (
    build_google_authorize_url,
    fetch_supabase_user,
    is_supabase_auth_enabled,
    supabase_password_sign_in,
    supabase_sign_up,
)
from app.auth.utils import encrypt_token
from app.database.database import get_db
from app.database.models import User
from app.i18n import resolve_locale, translate
from app.users.repository import UserRepository
from app.users.service import UserService
from config import Settings

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthSessionPayload(BaseModel):
    access_token: str
    refresh_token: str | None = None
    provider_token: str | None = None
    provider_refresh_token: str | None = None


class PasswordAuthPayload(BaseModel):
    email: EmailStr
    password: str


def _msg(request: Request, key: str, **kwargs) -> str:
    return translate(key, resolve_locale(request), **kwargs)


def _set_session_cookie(response: Response, session_token: str) -> None:
    settings = Settings()
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.JWT_EXPIRY_HOURS * 3600,
    )


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    settings = Settings()
    response.set_cookie(
        key="supabase_refresh",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=max(settings.JWT_EXPIRY_HOURS * 3600 * 4, 86400),
    )


def _upsert_local_user_from_profile(
    db,
    email: str,
    name: str,
    external_id: str,
    provider_token: str | None = None,
    provider_refresh_token: str | None = None,
) -> User:
    repo = UserRepository(db)
    user = repo.get_user_by_email(email.lower())

    if not user:
        user_id = str(uuid.uuid4())
        payload = {
            "id": user_id,
            "email": email.lower(),
            "name": name or email,
            "google_id": external_id,
            "last_login": datetime.utcnow().isoformat(),
        }
        if provider_token:
            payload["google_access_token"] = encrypt_token(provider_token)
        if provider_refresh_token:
            payload["google_refresh_token"] = encrypt_token(provider_refresh_token)
        user = repo.create_user(payload)
        cal = repo.create_calendar(
            {
                "id": str(uuid.uuid4()),
                "name": f"{(name or email)}'s Calendar",
                "owner_user_id": user_id,
            }
        )
        user = repo.update_user(user.id, {"calendar_id": cal.id}) or user
    else:
        update_payload = {
            "name": name or user.name,
            "google_id": user.google_id or external_id,
            "last_login": datetime.utcnow().isoformat(),
        }
        if not user.calendar_id:
            cal = repo.create_calendar(
                {
                    "id": str(uuid.uuid4()),
                    "name": f"{(name or email)}'s Calendar",
                    "owner_user_id": user.id,
                }
            )
            update_payload["calendar_id"] = cal.id
        if provider_token:
            update_payload["google_access_token"] = encrypt_token(provider_token)
        if provider_refresh_token:
            update_payload["google_refresh_token"] = encrypt_token(provider_refresh_token)
        user = repo.update_user(user.id, update_payload) or user

    service = UserService(db)
    service.accept_household_invitation(user.id)
    return user


@router.get("/login")
async def login():
    settings = Settings()
    if is_supabase_auth_enabled(settings):
        auth_url = build_google_authorize_url(settings.GOOGLE_REDIRECT_URI)
        return RedirectResponse(url=auth_url)

    auth_url, _state = get_authorization_url()
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def oauth_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db=Depends(get_db),
):
    settings = Settings()

    if error:
        raise HTTPException(status_code=400, detail=_msg(request, "auth.oauth_callback_failed", error=error))

    if not code:
        # Supabase OAuth implicit flow delivers tokens in URL fragment; JS forwards them to /auth/session.
        locale = resolve_locale(request)
        unknown_error = json.dumps(_msg(request, "sync.unknown"))
        return HTMLResponse(
            f"""
<!doctype html>
<html lang=\"{locale}\">
<head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>{_msg(request, "auth.signing_in")}</title></head>
<body>
  <p>{_msg(request, "auth.finalizing_sign_in")}</p>
  <script>
    (async function () {{
      try {{
        const hash = window.location.hash.startsWith('#') ? window.location.hash.substring(1) : '';
        const params = new URLSearchParams(hash);
        const payload = {{
          access_token: params.get('access_token'),
          refresh_token: params.get('refresh_token'),
          provider_token: params.get('provider_token'),
          provider_refresh_token: params.get('provider_refresh_token')
        }};
        if (!payload.access_token) {{
          document.body.innerHTML = '<p>{_msg(request, "auth.missing_oauth_access_token")}</p>';
          return;
        }}
        const response = await fetch('/auth/session', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(payload)
        }});
        if (!response.ok) {{
          const data = await response.json().catch(() => ({{}}));
          document.body.innerHTML = `<p>{_msg(request, "auth.sign_in_failed")}: ${{data.detail || {unknown_error}}}</p>`;
          return;
        }}
        window.location.href = '/';
      }} catch (err) {{
        document.body.innerHTML = `<p>{_msg(request, "auth.sign_in_failed")}: ${{String(err)}}</p>`;
      }}
    }})();
  </script>
</body>
</html>
            """.strip()
        )

    # Keep direct Google callback flow for backward compatibility and tests.
    try:
        tokens = exchange_code_for_token(code, state or "")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=_msg(request, "auth.oauth_callback_failed", error=str(exc))) from exc

    user_info = tokens["user_info"]
    if not user_info.get("email") or not user_info.get("google_id"):
        raise HTTPException(status_code=400, detail=_msg(request, "auth.missing_google_profile"))

    user = _upsert_local_user_from_profile(
        db=db,
        email=user_info["email"],
        name=user_info.get("name") or user_info["email"],
        external_id=user_info["google_id"],
        provider_token=tokens.get("access_token"),
        provider_refresh_token=tokens.get("refresh_token"),
    )

    UserRepository(db).update_user(user.id, {"google_token_expiry": tokens["token_expiry"].isoformat()})

    payload = {
        "user_id": str(user.id),
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRY_HOURS),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    response = RedirectResponse(url="/", status_code=302)
    _set_session_cookie(response, token)
    return response


@router.post("/session")
async def create_supabase_session(request: Request, payload: AuthSessionPayload, db=Depends(get_db)):
    profile = await fetch_supabase_user(payload.access_token)
    if not profile:
        raise HTTPException(status_code=401, detail=_msg(request, "auth.invalid_supabase_session"))

    email = (profile.get("email") or "").lower()
    if not email:
        raise HTTPException(status_code=400, detail=_msg(request, "auth.supabase_profile_missing_email"))

    metadata = profile.get("user_metadata") or {}
    name = metadata.get("full_name") or metadata.get("name") or email
    external_id = profile.get("id") or ""

    db_warning = None
    try:
        _upsert_local_user_from_profile(
            db=db,
            email=email,
            name=name,
            external_id=external_id,
            provider_token=payload.provider_token,
            provider_refresh_token=payload.provider_refresh_token,
        )
    except Exception:
        db_warning = "Authenticated via Supabase, but local database is unavailable right now."

    body = {"message": _msg(request, "auth.session_created")}
    if db_warning:
        body["warning"] = "local_db_unavailable"
    response = Response(content=json.dumps(body), media_type="application/json")
    _set_session_cookie(response, payload.access_token)
    if payload.refresh_token:
        _set_refresh_cookie(response, payload.refresh_token)
    return response


@router.post("/register")
async def register_with_password(request: Request, payload: PasswordAuthPayload, db=Depends(get_db)):
    settings = Settings()
    if not is_supabase_auth_enabled(settings):
        raise HTTPException(status_code=400, detail=_msg(request, "auth.supabase_not_configured"))

    try:
        data = await supabase_sign_up(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    access_token = data.get("access_token")
    user = data.get("user") or {}
    email = (user.get("email") or payload.email).lower()
    name = (user.get("user_metadata") or {}).get("full_name") or email
    external_id = user.get("id") or ""
    db_warning = None
    try:
        _upsert_local_user_from_profile(db, email, name, external_id)
    except Exception:
        db_warning = "registered_but_local_db_unavailable"

    if not access_token:
        if db_warning:
            return {
                "message": _msg(request, "auth.registration_created"),
                "warning": db_warning,
            }
        return {"message": _msg(request, "auth.registration_created")}

    body = {"message": _msg(request, "auth.registered")}
    if db_warning:
        body["warning"] = "registered_but_local_db_unavailable"
    response = Response(content=json.dumps(body), media_type="application/json")
    _set_session_cookie(response, access_token)
    if data.get("refresh_token"):
        _set_refresh_cookie(response, data["refresh_token"])
    return response


@router.post("/password-login")
async def login_with_password(request: Request, payload: PasswordAuthPayload, db=Depends(get_db)):
    settings = Settings()
    if not is_supabase_auth_enabled(settings):
        raise HTTPException(status_code=400, detail=_msg(request, "auth.supabase_not_configured"))

    try:
        data = await supabase_password_sign_in(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    access_token = data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail=_msg(request, "auth.no_access_token"))

    supabase_profile = await fetch_supabase_user(access_token)
    if not supabase_profile:
        raise HTTPException(status_code=401, detail=_msg(request, "auth.profile_fetch_failed"))

    email = (supabase_profile.get("email") or payload.email).lower()
    metadata = supabase_profile.get("user_metadata") or {}
    name = metadata.get("full_name") or metadata.get("name") or email
    external_id = supabase_profile.get("id") or ""
    db_warning = None
    try:
        _upsert_local_user_from_profile(db, email, name, external_id)
    except Exception:
        db_warning = "logged_in_but_local_db_unavailable"

    body = {"message": _msg(request, "auth.logged_in")}
    if db_warning:
        body["warning"] = "logged_in_but_local_db_unavailable"
    response = Response(content=json.dumps(body), media_type="application/json")
    _set_session_cookie(response, access_token)
    if data.get("refresh_token"):
        _set_refresh_cookie(response, data["refresh_token"])
    return response


@router.post("/logout")
async def logout(request: Request, response: Response):
    response.delete_cookie("session")
    response.delete_cookie("supabase_refresh")
    return {"message": _msg(request, "auth.logged_out")}
