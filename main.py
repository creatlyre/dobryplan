import json
import logging
import os
import sys
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from config import Settings

from app.auth.dependencies import get_current_user
from app.auth.routes import router as auth_router
from app.events.routes import router as events_router
from app.i18n import inject_template_i18n, set_locale_cookie_if_param
from app.licensing.middleware import LicenseCheckMiddleware
from app.middleware.auth_middleware import SessionValidationMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.budget.routes import router as budget_router
from app.budget.views import router as budget_views_router
from app.budget.income_routes import router as income_router
from app.budget.income_views import router as income_views_router
from app.budget.expense_routes import router as expense_router
from app.budget.expense_views import router as expense_views_router
from app.budget.overview_routes import router as overview_router
from app.budget.overview_views import router as overview_views_router
from app.sync.routes import router as sync_router
from app.users.routes import router as users_router
from app.views.calendar_routes import router as calendar_router
from app.notifications.routes import router as notifications_router
from app.notifications.views import router as notification_views_router
from app.shopping.routes import router as shopping_router
from app.shopping.views import router as shopping_views_router
from app.dashboard.routes import router as dashboard_router
from app.billing.routes import router as billing_router
from app.billing.views import router as billing_views_router

app = FastAPI(
    title="Synco",
    description="Shared household calendar & budget planner with Google Calendar sync",
    version="1.0.0",
    debug=os.getenv("DEBUG", "false").lower() == "true",
)

# --- Structured logging ---

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging():
    settings = Settings(_env_file=None) if os.getenv("TESTING") else Settings()
    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL)
    handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_FORMAT == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
        ))
    root.handlers = [handler]


setup_logging()

# --- Sentry ---

_settings = Settings(_env_file=None) if os.getenv("TESTING") else Settings()
if _settings.SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=_settings.SENTRY_DSN,
        environment=_settings.ENVIRONMENT,
        traces_sample_rate=0.1 if _settings.ENVIRONMENT == "production" else 1.0,
        send_default_pii=False,
    )

templates = Jinja2Templates(directory="app/templates")

app.mount("/static", StaticFiles(directory="public"), name="static")


class StaticCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=604800"
        return response


# --- Rate limiting ---

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Middleware (outermost first) ---

app.add_middleware(
    LicenseCheckMiddleware,
    environment=_settings.ENVIRONMENT,
    license_key=_settings.SYNCO_LICENSE_KEY,
    license_secret=_settings.SYNCO_LICENSE_SECRET,
)
app.add_middleware(SecurityHeadersMiddleware, environment=_settings.ENVIRONMENT)

if _settings.ALLOWED_ORIGINS:
    origins = [o.strip() for o in _settings.ALLOWED_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(StaticCacheMiddleware)
app.add_middleware(SessionValidationMiddleware)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(events_router)
app.include_router(calendar_router)
app.include_router(sync_router)
app.include_router(budget_router)
app.include_router(budget_views_router)
app.include_router(income_router)
app.include_router(income_views_router)
app.include_router(expense_router)
app.include_router(expense_views_router)
app.include_router(overview_router)
app.include_router(overview_views_router)
app.include_router(notifications_router)
app.include_router(notification_views_router)
app.include_router(shopping_router)
app.include_router(shopping_views_router)
app.include_router(dashboard_router)
app.include_router(billing_router)
app.include_router(billing_views_router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, user=Depends(get_current_user)):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/invite", response_class=HTMLResponse)
async def invite_page(request: Request, user=Depends(get_current_user)):
    context = inject_template_i18n(
        request,
        {
            "request": request,
            "user": user,
        },
    )
    response = templates.TemplateResponse(
        request=request, name="invite.html", context=context
    )
    set_locale_cookie_if_param(response, request)
    return response


@app.get("/health")
async def health():
    from app.database.database import get_db
    checks = {"app": "ok"}
    try:
        db = next(get_db())
        db.select("subscriptions", {"limit": "1"})
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}


@app.get("/health/ready")
async def health_ready():
    return {"status": "ready"}


@app.exception_handler(HTTPException)
async def auth_redirect_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401 and request.url.path in {"/", "/invite", "/dashboard"}:
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/auth/login", status_code=307)
    return await http_exception_handler(request, exc)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
