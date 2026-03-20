from __future__ import annotations

from app.budget.income_repository import MonthlyHoursRepository, AdditionalEarningsRepository
from app.budget.expense_repository import ExpenseRepository
from app.budget.repository import BudgetSettingsRepository

DEFAULT_HOURS = 160.0


class OverviewService:
    def __init__(
        self,
        settings_repo: BudgetSettingsRepository,
        hours_repo: MonthlyHoursRepository,
        earnings_repo: AdditionalEarningsRepository,
        expense_repo: ExpenseRepository,
    ):
        self.settings_repo = settings_repo
        self.hours_repo = hours_repo
        self.earnings_repo = earnings_repo
        self.expense_repo = expense_repo

    def get_year_overview(self, calendar_id: str, year: int) -> dict:
        settings = self.settings_repo.get_by_calendar(calendar_id)
        hours_list = self.hours_repo.get_by_calendar_year(calendar_id, year)
        earnings_list = self.earnings_repo.get_by_calendar_year(calendar_id, year)
        expenses_list = self.expense_repo.get_by_calendar_year(calendar_id, year)

        r1 = settings.rate_1 if settings else 0
        r2 = settings.rate_2 if settings else 0
        r3 = settings.rate_3 if settings else 0
        zus = settings.zus_costs if settings else 0
        acc = settings.accounting_costs if settings else 0
        initial_balance = settings.initial_balance if settings else 0

        hours_by_month = {h.month: h for h in hours_list}

        # Split earnings
        earnings_by_month: dict[int, float] = {}
        recurring_earnings_total = 0.0
        for e in earnings_list:
            if e.month == 0:
                recurring_earnings_total += e.amount
            else:
                earnings_by_month[e.month] = earnings_by_month.get(e.month, 0) + e.amount

        # Split expenses
        recurring_expense_total = 0.0
        onetime_by_month: dict[int, float] = {}
        onetime_items_by_month: dict[int, list] = {}
        for e in expenses_list:
            if e.month == 0 or e.recurring:
                recurring_expense_total += e.amount
            else:
                onetime_by_month[e.month] = onetime_by_month.get(e.month, 0) + e.amount
                onetime_items_by_month.setdefault(e.month, []).append(
                    {"id": e.id, "name": e.name, "amount": e.amount}
                )

        running_balance = initial_balance
        months = []

        for m in range(1, 13):
            h = hours_by_month.get(m)
            h1 = h.rate_1_hours if (h and h.rate_1_hours is not None) else DEFAULT_HOURS
            h2 = h.rate_2_hours if (h and h.rate_2_hours is not None) else DEFAULT_HOURS
            h3 = h.rate_3_hours if (h and h.rate_3_hours is not None) else DEFAULT_HOURS

            net = (r1 * h1) * 0.88 + (r2 * h2) * 0.88 + (r3 * h3) * 0.88 - (zus + acc)
            additional = earnings_by_month.get(m, 0) + recurring_earnings_total
            onetime_expenses = onetime_by_month.get(m, 0)

            monthly_balance = net + additional - recurring_expense_total - onetime_expenses
            running_balance += monthly_balance

            months.append({
                "month": m,
                "net": round(net, 2),
                "additional_earnings": round(additional, 2),
                "recurring_expenses": round(recurring_expense_total, 2),
                "onetime_expenses": round(onetime_expenses, 2),
                "onetime_items": onetime_items_by_month.get(m, []),
                "monthly_balance": round(monthly_balance, 2),
                "account_balance": round(running_balance, 2),
            })

        return {
            "year": year,
            "initial_balance": round(initial_balance, 2),
            "months": months,
        }
