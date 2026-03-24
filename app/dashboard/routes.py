from typing import Optional

from fastapi import APIRouter, Cookie, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.auth.dependencies import get_current_user
from app.dashboard.service import DashboardService
from app.database.database import get_db
from app.i18n import inject_template_i18n, set_locale_cookie_if_param

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    user=Depends(get_current_user),
    db=Depends(get_db),
    session: Optional[str] = Cookie(None),
):
    service = DashboardService(db, auth_token=session)

    all_today = service.get_today_events(user.calendar_id, user.id)
    today_events = all_today[:5]
    today_overflow = max(0, len(all_today) - 5)

    week_preview = service.get_week_preview(user.calendar_id, user.id)
    category_map = service.get_event_categories(user.calendar_id)
    budget_snapshot = service.get_budget_snapshot(user.calendar_id)
    top_categories = service.get_top_expense_categories(user.calendar_id)
    onetime_expenses = service.get_onetime_expenses(user.calendar_id)

    # Build expense category map for display
    expense_categories = {}
    try:
        cats = service.expense_service.list_categories(user.calendar_id)
        expense_categories = {c.id: c for c in cats}
    except Exception:
        pass

    # Build category name → i18n key map for translation
    _CAT_I18N_SLUGS = {
        "Groceries": "groceries", "Rent": "rent", "Utilities": "utilities",
        "Transport": "transport", "Entertainment": "entertainment",
        "Health": "health", "Education": "education", "Home": "home",
        "Clothing": "clothing", "Children": "children",
        "Personal Care": "personal_care", "Pets": "pets",
        "Events": "events", "Savings & Finance": "savings",
        "Travel": "travel", "Shopping": "shopping",
        "Electronics": "electronics", "Garden": "garden",
        "Loan": "loan", "Other": "other",
    }

    from datetime import datetime

    now = datetime.utcnow()
    month_keys = [
        "budget.income_month_jan", "budget.income_month_feb", "budget.income_month_mar",
        "budget.income_month_apr", "budget.income_month_may", "budget.income_month_jun",
        "budget.income_month_jul", "budget.income_month_aug", "budget.income_month_sep",
        "budget.income_month_oct", "budget.income_month_nov", "budget.income_month_dec",
    ]

    context = inject_template_i18n(
        request,
        {
            "request": request,
            "user": user,
            "now": now,
            "today_events": today_events,
            "today_overflow": today_overflow,
            "week_preview": week_preview,
            "category_map": category_map,
            "budget_snapshot": budget_snapshot,
            "top_categories": top_categories,
            "onetime_expenses": onetime_expenses,
            "expense_categories": expense_categories,
            "cat_i18n": {},  # placeholder, filled after inject
            "budget_month_key": month_keys[now.month - 1],
            "budget_year": now.year,
        },
    )

    # Now translate category names using the t() function from context
    t_fn = context.get("t")
    if t_fn:
        context["cat_i18n"] = {
            name: t_fn(f"budget.expense_category_{slug}")
            for name, slug in _CAT_I18N_SLUGS.items()
        }

    response = templates.TemplateResponse(
        request=request, name="dashboard.html", context=context,
    )
    set_locale_cookie_if_param(response, request)
    return response
