from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.auth.dependencies import get_current_user
from app.budget.repository import BudgetSettingsRepository
from app.budget.service import BudgetSettingsService
from app.database.database import get_db
from app.i18n import inject_template_i18n, set_locale_cookie_if_param

router = APIRouter(prefix="/budget", tags=["budget-views"])
templates = Jinja2Templates(directory="app/templates")


def _service(db) -> BudgetSettingsService:
    return BudgetSettingsService(BudgetSettingsRepository(db))


@router.get("/settings", response_class=HTMLResponse)
async def budget_settings_page(
    request: Request,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = _service(db)
    settings = service.get_settings(user.calendar_id)
    context = inject_template_i18n(
        request,
        {
            "request": request,
            "user": user,
            "settings": settings,
        },
    )
    response = templates.TemplateResponse(request=request, name="budget_settings.html", context=context)
    set_locale_cookie_if_param(response, request)
    return response
