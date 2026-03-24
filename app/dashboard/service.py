from datetime import datetime, timedelta

from app.events.service import EventService
from app.events.repository import EventRepository
from app.budget.overview_service import OverviewService, CarryForwardRepository
from app.budget.repository import BudgetSettingsRepository
from app.budget.income_repository import MonthlyHoursRepository, AdditionalEarningsRepository
from app.budget.expense_repository import ExpenseRepository
from app.budget.expense_service import ExpenseService


class DashboardService:
    def __init__(self, db, auth_token=None):
        self.auth_token = auth_token
        self.event_service = EventService(EventRepository(db))
        self.overview_service = OverviewService(
            BudgetSettingsRepository(db),
            MonthlyHoursRepository(db),
            AdditionalEarningsRepository(db),
            ExpenseRepository(db),
            CarryForwardRepository(db),
        )
        self.expense_service = ExpenseService(ExpenseRepository(db))

    def get_today_events(self, calendar_id: str, user_id: str) -> list:
        now = datetime.utcnow()
        return self.event_service.list_day_expanded(
            calendar_id, now.year, now.month, now.day,
            requesting_user_id=user_id,
        )

    def get_week_preview(self, calendar_id: str, user_id: str, days: int = 7) -> list[dict]:
        today = datetime.utcnow().date()
        result = []
        for offset in range(1, days + 1):
            day = today + timedelta(days=offset)
            events = self.event_service.list_day_expanded(
                calendar_id, day.year, day.month, day.day,
                requesting_user_id=user_id,
            )
            overflow = max(0, len(events) - 3)
            result.append({
                "date": day,
                "day_name": day.strftime("%a"),
                "events": events[:3],
                "overflow": overflow,
            })
        return result

    def get_event_categories(self, calendar_id: str) -> dict:
        categories = self.event_service.list_categories(calendar_id)
        return {cat.id: cat for cat in categories}

    def get_budget_snapshot(self, calendar_id: str) -> dict:
        now = datetime.utcnow()
        try:
            data = self.overview_service.get_year_overview(
                calendar_id, now.year, auth_token=self.auth_token,
            )
        except Exception:
            return {"has_data": False}

        if not data or not data.get("has_data"):
            return {"has_data": False}

        month_idx = now.month - 1
        months = data.get("months", [])
        if month_idx >= len(months):
            return {"has_data": False}

        m = months[month_idx]
        income = m.get("net", 0) + m.get("additional_earnings", 0)
        expenses = m.get("recurring_expenses", 0) + m.get("onetime_expenses", 0)
        return {
            "has_data": True,
            "account_balance": m.get("account_balance", 0),
            "monthly_balance": m.get("monthly_balance", 0),
            "income": round(income, 2),
            "expenses": round(expenses, 2),
        }

    def get_top_expense_categories(self, calendar_id: str, limit: int = 3) -> list[dict]:
        now = datetime.utcnow()
        try:
            breakdown = self.expense_service.get_category_breakdown(calendar_id, now.year)
        except Exception:
            return []
        return breakdown[:limit]

    def get_onetime_expenses(self, calendar_id: str) -> list[dict]:
        """Return one-time expenses for the current month."""
        now = datetime.utcnow()
        try:
            data = self.expense_service.get_year_data(calendar_id, now.year)
        except Exception:
            return []
        return [
            e for e in data.get("onetime_expenses", [])
            if e.get("month") == now.month
        ]
