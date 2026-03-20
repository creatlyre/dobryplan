import os
from datetime import datetime

from fastapi import Depends, FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.auth.dependencies import get_current_user
from app.auth.routes import router as auth_router
from app.events.routes import router as events_router
from app.i18n import inject_template_i18n, set_locale_cookie_if_param
from app.middleware.auth_middleware import SessionValidationMiddleware
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

app = FastAPI(
    title="CalendarPlanner",
    description="Shared household calendar with Google Calendar sync",
    version="1.0.0",
    debug=os.getenv("DEBUG", "false").lower() == "true",
)

templates = Jinja2Templates(directory="app/templates")

app.mount("/static", StaticFiles(directory="public"), name="static")
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


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, user=Depends(get_current_user)):
    context = inject_template_i18n(
        request,
        {
            "request": request,
            "user": user,
            "now": datetime.utcnow(),
        },
    )
    response = templates.TemplateResponse(
        "calendar.html",
        context,
    )
    set_locale_cookie_if_param(response, request)
    return response


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
        "invite.html",
        context,
    )
    set_locale_cookie_if_param(response, request)
    return response


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.exception_handler(HTTPException)
async def auth_redirect_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401 and request.url.path in {"/", "/invite"}:
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
