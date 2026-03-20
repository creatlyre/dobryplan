from __future__ import annotations

from app.budget.income_repository import MonthlyHoursRepository, AdditionalEarningsRepository
from app.budget.repository import BudgetSettingsRepository
from app.budget.income_schemas import MonthlyHoursUpdate, AdditionalEarningCreate
from app.database.models import MonthlyHours, AdditionalEarning

DEFAULT_HOURS = 160.0


class IncomeService:
    def __init__(
        self,
        hours_repo: MonthlyHoursRepository,
        earnings_repo: AdditionalEarningsRepository,
        settings_repo: BudgetSettingsRepository,
    ):
        self.hours_repo = hours_repo
        self.earnings_repo = earnings_repo
        self.settings_repo = settings_repo

    def get_year_data(self, calendar_id: str, year: int) -> dict:
        settings = self.settings_repo.get_by_calendar(calendar_id)
        hours_list = self.hours_repo.get_by_calendar_year(calendar_id, year)
        earnings_list = self.earnings_repo.get_by_calendar_year(calendar_id, year)

        hours_by_month = {h.month: h for h in hours_list}
        earnings_by_month: dict[int, list[AdditionalEarning]] = {}
        recurring_earnings: list[AdditionalEarning] = []
        for e in earnings_list:
            if e.month == 0:
                recurring_earnings.append(e)
            else:
                earnings_by_month.setdefault(e.month, []).append(e)

        r1 = settings.rate_1 if settings else 0
        r2 = settings.rate_2 if settings else 0
        r3 = settings.rate_3 if settings else 0
        zus = settings.zus_costs if settings else 0
        acc = settings.accounting_costs if settings else 0

        months = []
        for m in range(1, 13):
            h = hours_by_month.get(m)
            h1 = h.rate_1_hours if (h and h.rate_1_hours is not None) else DEFAULT_HOURS
            h2 = h.rate_2_hours if (h and h.rate_2_hours is not None) else DEFAULT_HOURS
            h3 = h.rate_3_hours if (h and h.rate_3_hours is not None) else DEFAULT_HOURS

            gross = r1 * h1 + r2 * h2 + r3 * h3
            net = (r1 * h1) * 0.88 + (r2 * h2) * 0.88 + (r3 * h3) * 0.88 - (zus + acc)

            month_earnings = [
                {"id": e.id, "name": e.name, "amount": e.amount}
                for e in earnings_by_month.get(m, [])
            ]
            recurring_entries = [
                {"id": e.id, "name": e.name, "amount": e.amount}
                for e in recurring_earnings
            ]

            months.append({
                "month": m,
                "rate_1_hours": h.rate_1_hours if h else None,
                "rate_2_hours": h.rate_2_hours if h else None,
                "rate_3_hours": h.rate_3_hours if h else None,
                "gross": round(gross, 2),
                "net": round(net, 2),
                "additional_earnings": month_earnings,
                "recurring_earnings": recurring_entries,
            })

        recurring_list = [
            {"id": e.id, "name": e.name, "amount": e.amount}
            for e in recurring_earnings
        ]
        return {"year": year, "months": months, "recurring_earnings": recurring_list}

    def save_hours(self, calendar_id: str, payload: MonthlyHoursUpdate) -> MonthlyHours:
        return self.hours_repo.upsert(calendar_id, payload)

    def add_earning(self, calendar_id: str, payload: AdditionalEarningCreate) -> AdditionalEarning:
        return self.earnings_repo.create(calendar_id, payload)

    def delete_earning(self, earning_id: str) -> bool:
        return self.earnings_repo.delete(earning_id)
