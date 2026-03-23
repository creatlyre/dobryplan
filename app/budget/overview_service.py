from __future__ import annotations

from datetime import datetime, timezone

from app.budget.income_repository import (
    MonthlyHoursRepository,
    AdditionalEarningsRepository,
)
from app.budget.expense_repository import ExpenseRepository
from app.budget.repository import BudgetSettingsRepository
from app.database.models import CarryForwardOverride
from app.database.supabase_store import SupabaseStore, SupabaseStoreError

DEFAULT_HOURS = 160.0


class CarryForwardRepository:
    def __init__(self, db: SupabaseStore):
        self.db = db

    def get(
        self, calendar_id: str, year: int, auth_token: str | None = None
    ) -> CarryForwardOverride | None:
        try:
            rows = self.db.select(
                "carry_forward_overrides",
                {
                    "calendar_id": f"eq.{calendar_id}",
                    "year": f"eq.{year}",
                    "limit": "1",
                },
                auth_token=auth_token,
            )
        except SupabaseStoreError:
            return None
        if not rows:
            return None
        r = rows[0]
        return CarryForwardOverride(
            id=r.get("id", ""),
            calendar_id=r.get("calendar_id", ""),
            year=int(r.get("year", 0)),
            amount=float(r.get("amount", 0)),
        )

    def upsert(
        self, calendar_id: str, year: int, amount: float, auth_token: str | None = None
    ) -> CarryForwardOverride:
        existing = self.get(calendar_id, year, auth_token=auth_token)
        if existing:
            row = self.db.update(
                "carry_forward_overrides",
                {"id": f"eq.{existing.id}"},
                {
                    "amount": amount,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                auth_token=auth_token,
            )
            if row:
                existing.amount = amount
            return existing
        row = self.db.insert(
            "carry_forward_overrides",
            {"calendar_id": calendar_id, "year": year, "amount": amount},
            auth_token=auth_token,
        )
        return CarryForwardOverride(
            id=row.get("id", ""),
            calendar_id=calendar_id,
            year=year,
            amount=amount,
        )

    def delete(
        self, calendar_id: str, year: int, auth_token: str | None = None
    ) -> bool:
        return (
            self.db.delete(
                "carry_forward_overrides",
                {"calendar_id": f"eq.{calendar_id}", "year": f"eq.{year}"},
                auth_token=auth_token,
            )
            > 0
        )


class OverviewService:
    def __init__(
        self,
        settings_repo: BudgetSettingsRepository,
        hours_repo: MonthlyHoursRepository,
        earnings_repo: AdditionalEarningsRepository,
        expense_repo: ExpenseRepository,
        carry_forward_repo: CarryForwardRepository | None = None,
    ):
        self.settings_repo = settings_repo
        self.hours_repo = hours_repo
        self.earnings_repo = earnings_repo
        self.expense_repo = expense_repo
        self.carry_forward_repo = carry_forward_repo

    def get_year_bounds(self, calendar_id: str) -> dict:
        current_year = datetime.now().year
        expense_years = self.expense_repo.get_distinct_years(calendar_id)
        hours_years = self.hours_repo.get_distinct_years(calendar_id)
        earnings_years = self.earnings_repo.get_distinct_years(calendar_id)
        all_years = sorted(set(expense_years + hours_years + earnings_years))
        if not all_years:
            return {"min_year": current_year, "max_year": current_year + 1}
        return {
            "min_year": min(all_years),
            "max_year": max(max(all_years), current_year) + 1,
        }

    def _year_has_data(self, calendar_id: str, year: int) -> bool:
        hours = self.hours_repo.get_by_calendar_year(calendar_id, year)
        if hours:
            return True
        earnings = self.earnings_repo.get_by_calendar_year(calendar_id, year)
        year_specific_earnings = [e for e in earnings if e.month != 0]
        if year_specific_earnings:
            return True
        expenses = self.expense_repo.get_by_calendar_year(calendar_id, year)
        year_specific_expenses = [
            e for e in expenses if e.month != 0 and not e.recurring
        ]
        if year_specific_expenses:
            return True
        return False

    def _compute_carry_forward(
        self,
        calendar_id: str,
        year: int,
        settings,
        auth_token: str | None = None,
        prior_overview: dict | None = None,
        bounds: dict | None = None,
    ) -> dict:
        # Check for manual override first
        if self.carry_forward_repo:
            override = self.carry_forward_repo.get(
                calendar_id, year, auth_token=auth_token
            )
            if override:
                return {
                    "type": "override",
                    "amount": round(override.amount, 2),
                    "source_year": year - 1,
                }

        if bounds is None:
            bounds = self.get_year_bounds(calendar_id)
        global_initial = settings.initial_balance if settings else 0

        if year <= bounds["min_year"]:
            return {
                "type": "initial",
                "amount": round(global_initial, 2),
                "source_year": None,
            }

        prior_year = year - 1
        if prior_overview is not None:
            prior_has_data = prior_overview.get("has_data", False)
        else:
            prior_has_data = self._year_has_data(calendar_id, prior_year)

        if not prior_has_data:
            return {"type": "no_prior_data", "amount": 0, "source_year": prior_year}

        if prior_overview is None:
            prior_overview = self.get_year_overview(
                calendar_id, prior_year, auth_token=auth_token, bounds=bounds
            )

        dec_balance = prior_overview["months"][11]["account_balance"]
        return {
            "type": "carry_forward",
            "amount": round(dec_balance, 2),
            "source_year": prior_year,
        }

    def _get_prior_december_net(
        self, calendar_id: str, year: int, prior_overview: dict | None = None
    ) -> float:
        """Net income for December of (year-1), used as January salary offset.

        Salary earned in month N is paid ~10th of month N+1, so
        monthly_balance uses previous month's net instead of current.
        """
        if prior_overview is not None:
            return prior_overview["months"][11]["net"]

        prior_year = year - 1
        settings = self.settings_repo.get_by_calendar(calendar_id, year=prior_year)
        if not settings:
            settings = self.settings_repo.get_by_calendar(calendar_id, year=year)
        if not settings:
            return 0.0

        r1, r2, r3 = settings.rate_1, settings.rate_2, settings.rate_3
        zus, acc = settings.zus_costs, settings.accounting_costs

        hours_list = self.hours_repo.get_by_calendar_year(calendar_id, prior_year)
        hours_by_month = {h.month: h for h in hours_list}
        h = hours_by_month.get(12)

        if h is None:
            # No prior year December data — use January of current year as proxy
            current_hours = self.hours_repo.get_by_calendar_year(calendar_id, year)
            h = {ch.month: ch for ch in current_hours}.get(1)

        h1 = h.rate_1_hours if (h and h.rate_1_hours is not None) else DEFAULT_HOURS
        h2 = h.rate_2_hours if (h and h.rate_2_hours is not None) else DEFAULT_HOURS
        h3 = h.rate_3_hours if (h and h.rate_3_hours is not None) else DEFAULT_HOURS

        return (r1 * h1) * 0.88 + (r2 * h2) * 0.88 + (r3 * h3) * 0.88 - (zus + acc)

    def get_year_overview(
        self,
        calendar_id: str,
        year: int,
        auth_token: str | None = None,
        prior_overview: dict | None = None,
        bounds: dict | None = None,
    ) -> dict:
        settings = self.settings_repo.get_by_calendar(calendar_id, year=year)
        hours_list = self.hours_repo.get_by_calendar_year(calendar_id, year)
        earnings_list = self.earnings_repo.get_by_calendar_year(calendar_id, year)
        expenses_list = self.expense_repo.get_by_calendar_year(calendar_id, year)

        r1 = settings.rate_1 if settings else 0
        r2 = settings.rate_2 if settings else 0
        r3 = settings.rate_3 if settings else 0
        zus = settings.zus_costs if settings else 0
        acc = settings.accounting_costs if settings else 0

        carry_forward = self._compute_carry_forward(
            calendar_id,
            year,
            settings,
            auth_token=auth_token,
            prior_overview=prior_overview,
            bounds=bounds,
        )
        effective_initial = carry_forward["amount"]

        # Pre-compute fixed costs and rate coefficients
        base_deductions = zus + acc
        c1, c2, c3 = r1 * 0.88, r2 * 0.88, r3 * 0.88
        default_net = (
            c1 * DEFAULT_HOURS
            + c2 * DEFAULT_HOURS
            + c3 * DEFAULT_HOURS
            - base_deductions
        )

        # Pre-populate net array
        nets = [default_net] * 13
        for h in hours_list:
            if 1 <= h.month <= 12:
                h1 = h.rate_1_hours if h.rate_1_hours is not None else DEFAULT_HOURS
                h2 = h.rate_2_hours if h.rate_2_hours is not None else DEFAULT_HOURS
                h3 = h.rate_3_hours if h.rate_3_hours is not None else DEFAULT_HOURS
                nets[h.month] = c1 * h1 + c2 * h2 + c3 * h3 - base_deductions

        # Split earnings
        earnings_by_month = [0.0] * 13
        recurring_earnings_total = 0.0
        for e in earnings_list:
            if e.month == 0:
                recurring_earnings_total += e.amount
            elif 1 <= e.month <= 12:
                earnings_by_month[e.month] += e.amount

        # Split expenses
        recurring_expense_total = 0.0
        onetime_by_month = [0.0] * 13
        onetime_items_by_month: list[list[dict]] = [[] for _ in range(13)]
        for e in expenses_list:
            if e.month == 0 or e.recurring:
                recurring_expense_total += e.amount
            elif 1 <= e.month <= 12:
                onetime_by_month[e.month] += e.amount
                onetime_items_by_month[e.month].append(
                    {"id": e.id, "name": e.name, "amount": e.amount}
                )

        running_balance = effective_initial
        months = []

        # Salary offset: salary earned in month N is received in month N+1.
        # January uses December of prior year; subsequent months use prior month.
        prev_net = self._get_prior_december_net(calendar_id, year, prior_overview)

        for m in range(1, 13):
            net = nets[m]
            additional = earnings_by_month[m] + recurring_earnings_total
            onetime_expenses = onetime_by_month[m]

            monthly_balance = (
                prev_net + additional - recurring_expense_total - onetime_expenses
            )
            running_balance += monthly_balance
            prev_net = net

            months.append(
                {
                    "month": m,
                    "net": round(net, 2),
                    "additional_earnings": round(additional, 2),
                    "recurring_expenses": round(recurring_expense_total, 2),
                    "onetime_expenses": round(onetime_expenses, 2),
                    "onetime_items": onetime_items_by_month[m],
                    "monthly_balance": round(monthly_balance, 2),
                    "account_balance": round(running_balance, 2),
                }
            )

        has_data = bool(hours_list)
        if not has_data:
            has_data = any(e.month != 0 for e in earnings_list)
        if not has_data:
            has_data = any(e.month != 0 and not e.recurring for e in expenses_list)

        return {
            "year": year,
            "has_data": has_data,
            "initial_balance": round(effective_initial, 2),
            "carry_forward": carry_forward,
            "months": months,
        }

    def get_year_comparison(
        self, calendar_id: str, year: int, auth_token: str | None = None
    ) -> dict:
        bounds = self.get_year_bounds(calendar_id)
        previous = self.get_year_overview(
            calendar_id, year - 1, auth_token=auth_token, bounds=bounds
        )
        selected = self.get_year_overview(
            calendar_id,
            year,
            auth_token=auth_token,
            prior_overview=previous,
            bounds=bounds,
        )

        def _sum_totals(data: dict) -> dict:
            months = data["months"]
            return {
                "total_net": round(sum(m["net"] for m in months), 2),
                "total_additional": round(
                    sum(m["additional_earnings"] for m in months), 2
                ),
                "total_recurring": round(
                    sum(m["recurring_expenses"] for m in months), 2
                ),
                "total_onetime": round(sum(m["onetime_expenses"] for m in months), 2),
                "total_balance": round(sum(m["monthly_balance"] for m in months), 2),
                "final_account_balance": (
                    round(months[-1]["account_balance"], 2) if months else 0.0
                ),
            }

        sel_totals = _sum_totals(selected)
        prev_totals = _sum_totals(previous)

        delta = {
            key: round(sel_totals[key] - prev_totals[key], 2) for key in sel_totals
        }

        return {
            "selected_year": year,
            "previous_year": year - 1,
            "selected": sel_totals,
            "previous": prev_totals,
            "delta": delta,
        }
