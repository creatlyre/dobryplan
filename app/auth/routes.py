from datetime import datetime, timedelta
import json
import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, EmailStr

from fastapi.templating import Jinja2Templates

from app.auth.oauth import exchange_code_for_token, get_authorization_url
from app.auth.supabase_auth import (
    build_google_authorize_url,
    fetch_supabase_user,
    is_supabase_auth_enabled,
    supabase_password_sign_in,
    supabase_request_password_reset,
    supabase_sign_up,
    supabase_update_user_password,
    supabase_verify_otp,
)
from app.auth.utils import encrypt_token
from app.database.database import get_db
from app.database.models import User
from app.i18n import inject_template_i18n, resolve_locale, translate
from app.users.repository import UserRepository
from app.users.service import UserService
from config import Settings

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


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
        secure=settings.ENVIRONMENT != "development",
        samesite="lax",
        max_age=settings.SESSION_COOKIE_MAX_AGE,
    )


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    settings = Settings()
    response.set_cookie(
        key="supabase_refresh",
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT != "development",
        samesite="lax",
        max_age=settings.REFRESH_COOKIE_MAX_AGE,
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
async def login_page(request: Request, provider: str | None = None, db=Depends(get_db)):
    settings = Settings()
    if provider == "google":
        if is_supabase_auth_enabled(settings):
            auth_url = build_google_authorize_url(settings.GOOGLE_REDIRECT_URI)
            return RedirectResponse(url=auth_url)
        auth_url, _state = get_authorization_url()
        return RedirectResponse(url=auth_url)

    context = inject_template_i18n(request, {"request": request})
    return templates.TemplateResponse(request, "login.html", context)


@router.get("/register")
async def register_page(request: Request):
    context = inject_template_i18n(request, {"request": request})
    return templates.TemplateResponse(request, "register.html", context)


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
        app_name = _msg(request, "app.name")
        return HTMLResponse(
            f"""
<!doctype html>
<html lang="{locale}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_msg(request, "auth.signing_in")} — {app_name}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Plus+Jakarta+Sans:wght@600;700&display=swap" rel="stylesheet">
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    body{{
      font-family:'DM Sans',ui-sans-serif,system-ui,sans-serif;
      background:#0f0a2e;
      min-height:100vh;display:flex;align-items:center;justify-content:center;
      color:rgba(255,255,255,.9);
      position:relative;overflow:hidden;
    }}
    .bg-layer{{
      position:fixed;inset:0;z-index:0;
    }}
    .bg-layer img{{width:100%;height:100%;object-fit:cover;opacity:.35;}}
    .bg-layer .overlay{{
      position:absolute;inset:0;
      background:linear-gradient(180deg,rgba(15,10,46,.5) 0%,rgba(15,10,46,.85) 70%,#0f0a2e 100%);
    }}
    .bg-glow{{
      position:fixed;inset:0;z-index:0;
      background:radial-gradient(ellipse 80% 60% at 50% 30%,rgba(99,102,241,.18) 0%,rgba(139,92,246,.06) 40%,transparent 70%);
    }}
    .card{{
      position:relative;z-index:1;
      text-align:center;padding:2.5rem 2rem;border-radius:1.25rem;
      background:rgba(255,255,255,.07);
      backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);
      border:1px solid rgba(255,255,255,.16);
      box-shadow:0 8px 32px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.12);
      max-width:360px;width:90%;animation:fadeIn .5s ease-out;
    }}
    .brand{{
      font-family:'Plus Jakarta Sans',ui-sans-serif,system-ui,sans-serif;
      font-weight:700;font-size:1.5rem;letter-spacing:-.02em;
      margin-bottom:1.75rem;display:flex;align-items:center;justify-content:center;gap:.5rem;
    }}
    .brand img{{width:1.75rem;height:1.75rem;border-radius:.375rem;}}
    .spinner{{
      width:2.5rem;height:2.5rem;margin:0 auto 1.25rem;
      border:3px solid rgba(255,255,255,.12);
      border-top-color:#a5b4fc;border-radius:50%;
      animation:spin .8s linear infinite;
    }}
    .status{{font-size:.9375rem;color:rgba(255,255,255,.7);line-height:1.5}}
    .error{{
      color:#fca5a5;background:rgba(239,68,68,.12);
      border:1px solid rgba(239,68,68,.25);border-radius:.75rem;
      padding:.75rem 1rem;font-size:.8125rem;line-height:1.5;
      margin-top:1.25rem;word-break:break-word;display:none;
    }}
    .retry{{
      display:none;margin-top:1rem;
      color:#fff;background:linear-gradient(135deg,rgba(99,102,241,.82),rgba(139,92,246,.82));
      border:1px solid rgba(139,92,246,.42);border-radius:.75rem;
      padding:.625rem 1.5rem;font-size:.875rem;font-weight:500;cursor:pointer;
      font-family:inherit;transition:filter .18s,transform .12s;
    }}
    .retry:hover{{filter:brightness(1.18);transform:translateY(-1px)}}
    @keyframes spin{{to{{transform:rotate(360deg)}}}}
    @keyframes fadeIn{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:translateY(0)}}}}
  </style>
</head>
<body>
  <div class="bg-layer">
    <img src="/static/images/hero-bg.webp" alt="" aria-hidden="true">
    <div class="overlay"></div>
  </div>
  <div class="bg-glow"></div>
  <div class="card">
    <div class="brand">
      <img src="/static/images/logo-mark.webp" alt="" aria-hidden="true">
      {app_name}
    </div>
    <div class="spinner" id="spinner"></div>
    <p class="status" id="status">{_msg(request, "auth.finalizing_sign_in")}</p>
    <div class="error" id="error"></div>
    <button class="retry" id="retry" onclick="window.location.href='/auth/login'">{_msg(request, "auth.try_again")}</button>
  </div>
  <script>
    (async function () {{
      const statusEl = document.getElementById('status');
      const errorEl = document.getElementById('error');
      const spinnerEl = document.getElementById('spinner');
      const retryEl = document.getElementById('retry');
      function showError(msg) {{
        spinnerEl.style.display = 'none';
        statusEl.style.display = 'none';
        errorEl.textContent = msg;
        errorEl.style.display = 'block';
        retryEl.style.display = 'inline-block';
      }}
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
          showError('{_msg(request, "auth.missing_oauth_access_token")}');
          return;
        }}
        const response = await fetch('/auth/session', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(payload)
        }});
        if (!response.ok) {{
          const data = await response.json().catch(() => ({{}}));
          showError(`{_msg(request, "auth.sign_in_failed")}: ` + (data.detail || {unknown_error}));
          return;
        }}
        window.location.href = '/dashboard';
      }} catch (err) {{
        showError(`{_msg(request, "auth.sign_in_failed")}: ` + String(err));
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

    response = RedirectResponse(url="/dashboard", status_code=302)
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
async def logout(request: Request):
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie("session")
    response.delete_cookie("supabase_refresh")
    return response


@router.get("/logout")
async def logout_page(request: Request):
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("session")
    response.delete_cookie("supabase_refresh")
    return response


class ForgotPasswordPayload(BaseModel):
    email: EmailStr


class UpdatePasswordPayload(BaseModel):
    password: str


@router.get("/forgot-password")
async def forgot_password_page(request: Request):
    context = inject_template_i18n(request, {"request": request})
    return templates.TemplateResponse(request, "forgot_password.html", context)


@router.post("/forgot-password")
async def forgot_password_submit(request: Request, payload: ForgotPasswordPayload):
    settings = Settings()
    if not is_supabase_auth_enabled(settings):
        raise HTTPException(status_code=400, detail=_msg(request, "auth.supabase_not_configured"))
    base_url = str(request.base_url).rstrip("/")
    redirect_to = f"{base_url}/auth/confirm"
    try:
        await supabase_request_password_reset(payload.email, redirect_to)
    except ValueError:
        pass  # Don't reveal whether email exists
    return {"message": _msg(request, "auth.reset_email_sent")}


@router.get("/confirm")
async def confirm_callback(
    request: Request,
    token_hash: str | None = None,
    type: str | None = None,
    next: str | None = None,
    db=Depends(get_db),
):
    if not token_hash or not type:
        return RedirectResponse(url="/auth/login", status_code=302)

    try:
        data = await supabase_verify_otp(token_hash, type)
    except ValueError:
        return RedirectResponse(url="/auth/login", status_code=302)

    access_token = data.get("access_token")
    if not access_token:
        return RedirectResponse(url="/auth/login", status_code=302)

    # Upsert local user
    profile = await fetch_supabase_user(access_token)
    if profile:
        email = (profile.get("email") or "").lower()
        metadata = profile.get("user_metadata") or {}
        name = metadata.get("full_name") or metadata.get("name") or email
        external_id = profile.get("id") or ""
        try:
            _upsert_local_user_from_profile(db, email, name, external_id)
        except Exception:
            pass

    # Determine redirect
    if type == "recovery":
        redirect_url = next or "/auth/update-password"
    else:
        redirect_url = next or "/dashboard"

    response = RedirectResponse(url=redirect_url, status_code=302)
    _set_session_cookie(response, access_token)
    if data.get("refresh_token"):
        _set_refresh_cookie(response, data["refresh_token"])
    return response


@router.get("/update-password")
async def update_password_page(request: Request):
    session = request.cookies.get("session")
    if not session:
        return RedirectResponse(url="/auth/login", status_code=302)
    context = inject_template_i18n(request, {"request": request})
    return templates.TemplateResponse(request, "update_password.html", context)


@router.post("/update-password")
async def update_password_submit(request: Request, payload: UpdatePasswordPayload):
    session = request.cookies.get("session")
    if not session:
        raise HTTPException(status_code=401, detail=_msg(request, "auth.not_authenticated"))
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail=_msg(request, "auth.password_min_length"))
    try:
        await supabase_update_user_password(session, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": _msg(request, "auth.password_updated")}
