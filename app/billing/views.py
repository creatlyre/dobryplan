from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.auth.dependencies import get_current_user
from app.billing.dependencies import get_user_plan_for_template
from app.billing.repository import BillingRepository
from app.database.database import get_db
from app.i18n import inject_template_i18n, set_locale_cookie_if_param

router = APIRouter(prefix="/billing", tags=["billing-views"])
public_router = APIRouter(tags=["billing-public"])
templates = Jinja2Templates(directory="app/templates")


@public_router.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    context = inject_template_i18n(request, {"request": request})
    response = templates.TemplateResponse(request=request, name="pricing.html", context=context)
    set_locale_cookie_if_param(response, request)
    return response


@router.get("/settings", response_class=HTMLResponse)
async def billing_settings_page(
    request: Request,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    repo = BillingRepository(db)
    sub = repo.get_subscription(user.id)

    plan = sub.plan if sub else "free"
    status = sub.status if sub else "active"
    current_period_end = sub.current_period_end if sub else None
    cancel_at_period_end = sub.cancel_at_period_end if sub else False
    has_stripe_customer = bool(sub and sub.stripe_customer_id)

    context = inject_template_i18n(
        request,
        {
            "request": request,
            "user": user,
            "user_plan": plan,
            "plan_status": status,
            "current_period_end": current_period_end,
            "cancel_at_period_end": cancel_at_period_end,
            "has_stripe_customer": has_stripe_customer,
        },
    )

    response = templates.TemplateResponse(
        request=request, name="billing_settings.html", context=context,
    )
    set_locale_cookie_if_param(response, request)
    return response
