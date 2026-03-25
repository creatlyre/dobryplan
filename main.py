import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from starlette.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from config import Settings

from app.auth.dependencies import get_current_user, get_current_user_optional
from app.billing.dependencies import get_user_plan_for_template, UpgradeRedirect
from app.database.database import get_db
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
from app.billing.views import public_router as billing_public_router
from app.admin.routes import router as admin_router
from app.admin.views import router as admin_views_router
from app.licensing.routes import router as telemetry_router
from app.licensing.telemetry import (
    get_or_create_install_id,
    build_heartbeat_payload,
    send_heartbeat_async,
    TelemetryReporter,
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Dobry Plan",
    description="Shared household calendar & budget planner with Google Calendar sync",
    version="1.0.0",
    debug=os.getenv("DEBUG", "false").lower() == "true",
)

# Cache-busting version: changes on each server restart / deploy
_ASSET_VERSION = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

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
templates.env.globals["asset_version"] = _ASSET_VERSION


@app.get("/manifest.json", include_in_schema=False)
async def pwa_manifest():
    return FileResponse("public/manifest.json", media_type="application/manifest+json")


@app.get("/sw.js", include_in_schema=False)
async def pwa_service_worker():
    return FileResponse(
        "public/sw.js",
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"},
    )


SITE_URL = "https://dobryplan.app"


@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /auth/\n"
        "Disallow: /admin/\n"
        "Disallow: /billing/\n"
        "Disallow: /api/\n"
        f"\nSitemap: {SITE_URL}/sitemap.xml\n"
    )
    return Response(content=content, media_type="text/plain")


@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml():
    from datetime import date

    today = date.today().isoformat()
    urls = [
        (f"{SITE_URL}/", "1.0", "weekly"),
        (f"{SITE_URL}/pricing", "0.8", "monthly"),
        (f"{SITE_URL}/terms", "0.3", "yearly"),
        (f"{SITE_URL}/privacy", "0.3", "yearly"),
        (f"{SITE_URL}/refund", "0.3", "yearly"),
        (f"{SITE_URL}/auth/login", "0.5", "monthly"),
        (f"{SITE_URL}/auth/register", "0.6", "monthly"),
    ]
    items = ""
    for loc, priority, freq in urls:
        items += (
            f"  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            f"    <changefreq>{freq}</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            f"  </url>\n"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{items}"
        "</urlset>\n"
    )
    return Response(content=xml, media_type="application/xml")


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


async def _upgrade_redirect_handler(request: Request, exc: UpgradeRedirect):
    context = inject_template_i18n(request, {
        "request": request,
        "feature": exc.feature,
    })
    return templates.TemplateResponse(
        request=request,
        name="upgrade_required.html",
        context=context,
        status_code=403,
    )


app.add_exception_handler(UpgradeRedirect, _upgrade_redirect_handler)

# --- Middleware (outermost first) ---

app.add_middleware(
    LicenseCheckMiddleware,
    environment=_settings.ENVIRONMENT,
    license_key=_settings.DOBRYPLAN_LICENSE_KEY,
    license_secret=_settings.DOBRYPLAN_LICENSE_SECRET,
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
app.include_router(billing_public_router)
app.include_router(admin_router)
app.include_router(admin_views_router)
app.include_router(telemetry_router)


# ── Telemetry: license compliance tracking ──────────────────────────────

_telemetry_reporter: TelemetryReporter | None = None


@app.on_event("startup")
def _start_telemetry():
    global _telemetry_reporter
    endpoint = _settings.TELEMETRY_ENDPOINT
    if not endpoint:
        logger.info("TELEMETRY_ENDPOINT not set — installation tracking disabled")
        return

    install_id = get_or_create_install_id()
    license_valid = False
    if _settings.DOBRYPLAN_LICENSE_KEY and _settings.DOBRYPLAN_LICENSE_SECRET:
        from app.licensing.keys import validate_license_key
        license_valid = validate_license_key(
            _settings.DOBRYPLAN_LICENSE_KEY, _settings.DOBRYPLAN_LICENSE_SECRET
        )

    # Fire an immediate heartbeat (non-blocking)
    payload = build_heartbeat_payload(
        install_id=install_id,
        license_valid=license_valid,
        environment=_settings.ENVIRONMENT,
    )
    send_heartbeat_async(endpoint, payload)

    # Start periodic reporter
    _telemetry_reporter = TelemetryReporter(
        endpoint=endpoint,
        install_id=install_id,
        license_valid=license_valid,
        environment=_settings.ENVIRONMENT,
        interval=_settings.TELEMETRY_INTERVAL,
    )
    _telemetry_reporter.start()


@app.on_event("shutdown")
def _stop_telemetry():
    if _telemetry_reporter:
        _telemetry_reporter.stop()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, user=Depends(get_current_user_optional)):
    from fastapi.responses import RedirectResponse
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    context = inject_template_i18n(request, {"request": request})
    response = templates.TemplateResponse(request=request, name="landing.html", context=context)
    set_locale_cookie_if_param(response, request)
    return response


@app.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    context = inject_template_i18n(request, {"request": request})
    response = templates.TemplateResponse(request=request, name="terms.html", context=context)
    set_locale_cookie_if_param(response, request)
    return response


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    context = inject_template_i18n(request, {"request": request})
    response = templates.TemplateResponse(request=request, name="privacy.html", context=context)
    set_locale_cookie_if_param(response, request)
    return response


@app.get("/refund", response_class=HTMLResponse)
async def refund_page(request: Request):
    context = inject_template_i18n(request, {"request": request})
    response = templates.TemplateResponse(request=request, name="refund.html", context=context)
    set_locale_cookie_if_param(response, request)
    return response


@app.get("/invite", response_class=HTMLResponse)
async def invite_page(request: Request, user=Depends(get_current_user), db=Depends(get_db)):
    context = inject_template_i18n(
        request,
        {
            "request": request,
            "user": user,
            "user_plan": get_user_plan_for_template(user, db),
        },
    )
    response = templates.TemplateResponse(
        request=request, name="invite.html", context=context
    )
    set_locale_cookie_if_param(response, request)
    return response


@app.get("/health")
async def health():
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
    if exc.status_code == 401 and request.url.path in {"/invite", "/dashboard"}:
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/auth/login", status_code=302)
    if exc.status_code == 403 and request.url.path.startswith("/admin"):
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/dashboard", status_code=302)
    return await http_exception_handler(request, exc)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
