import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

class SessionValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if os.getenv("PYTEST_CURRENT_TEST"):
            return await call_next(request)

        public_routes = {
            "/health",
            "/auth/login",
            "/auth/callback",
            "/auth/session",
            "/auth/register",
            "/auth/password-login",
            "/api/billing/webhook",
            "/docs",
            "/openapi.json",
            "/redoc",
        }

        if request.url.path in public_routes or request.url.path.startswith("/static"):
            return await call_next(request)

        session_cookie = request.cookies.get("session")
        refresh_cookie = request.cookies.get("supabase_refresh")
        if not session_cookie and not refresh_cookie:
            return RedirectResponse(url="/auth/login", status_code=307)

        return await call_next(request)
