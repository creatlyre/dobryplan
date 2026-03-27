from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.auth.dependencies import get_current_user
from app.billing.dependencies import get_user_plan_for_template
from app.database.database import get_db
from app.i18n import inject_template_i18n, set_locale_cookie_if_param

router = APIRouter(prefix="/budget", tags=["expense-views"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/expenses", response_class=HTMLResponse)
async def expenses_page(
    request: Request,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    context = inject_template_i18n(
        request,
        {
            "request": request,
            "user": user,
            "user_plan": get_user_plan_for_template(user, db),
        },
    )
    response = templates.TemplateResponse(request=request, name="budget_expenses.html", context=context)
    set_locale_cookie_if_param(response, request)
    return response


@router.get("/quick-expense", response_class=HTMLResponse)
async def quick_expense_page(
    request: Request,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    context = inject_template_i18n(
        request,
        {
            "request": request,
            "user": user,
            "user_plan": get_user_plan_for_template(user, db),
            "auto_open_quick_expense": True,
        },
    )
    response = templates.TemplateResponse(request=request, name="budget_expenses.html", context=context)
    set_locale_cookie_if_param(response, request)
    return response
