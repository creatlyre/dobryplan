from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.i18n import inject_template_i18n, set_locale_cookie_if_param

router = APIRouter(prefix="/budget", tags=["overview-views"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=RedirectResponse)
async def budget_root():
    return RedirectResponse(url="/budget/overview", status_code=302)


@router.get("/overview", response_class=HTMLResponse)
async def overview_page(
    request: Request,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    context = inject_template_i18n(
        request,
        {
            "request": request,
            "user": user,
        },
    )
    response = templates.TemplateResponse(request=request, name="budget_overview.html", context=context)
    set_locale_cookie_if_param(response, request)
    return response


@router.get("/import", response_class=HTMLResponse)
async def import_page(
    request: Request,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    context = inject_template_i18n(
        request,
        {"request": request, "user": user},
    )
    response = templates.TemplateResponse(request=request, name="budget_import.html", context=context)
    set_locale_cookie_if_param(response, request)
    return response
