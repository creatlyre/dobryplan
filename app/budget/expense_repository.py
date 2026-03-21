from __future__ import annotations

from datetime import datetime, timezone

from app.database.models import Expense
from app.database.supabase_store import SupabaseStore
from app.budget.expense_schemas import ExpenseCreate, ExpenseUpdate


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is not None:
            return parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    except ValueError:
        return None


def _to_expense(row: dict) -> Expense:
    return Expense(
        id=row.get("id", ""),
        calendar_id=row.get("calendar_id", ""),
        year=int(row.get("year", 0)),
        month=int(row.get("month", 0)),
        name=row.get("name", ""),
        amount=float(row.get("amount", 0)),
        recurring=bool(row.get("recurring", False)),
        created_at=_parse_dt(row.get("created_at")),
        updated_at=_parse_dt(row.get("updated_at")),
    )


class ExpenseRepository:
    def __init__(self, db: SupabaseStore):
        self.db = db

    def get_by_calendar_year(self, calendar_id: str, year: int) -> list[Expense]:
        rows = self.db.select(
            "expenses",
            {"calendar_id": f"eq.{calendar_id}", "year": f"eq.{year}"},
        )
        return [_to_expense(row) for row in rows]

    def create(self, calendar_id: str, payload: ExpenseCreate) -> Expense:
        row = self.db.insert(
            "expenses",
            {
                "calendar_id": calendar_id,
                "year": payload.year,
                "month": payload.month,
                "name": payload.name,
                "amount": payload.amount,
                "recurring": payload.recurring,
            },
        )
        return _to_expense(row)

    def update(self, expense_id: str, payload: ExpenseUpdate) -> Expense | None:
        data: dict = {"updated_at": datetime.utcnow().isoformat()}
        if payload.name is not None:
            data["name"] = payload.name
        if payload.amount is not None:
            data["amount"] = payload.amount
        if payload.month is not None:
            data["month"] = payload.month
            data["recurring"] = payload.month == 0
        row = self.db.update("expenses", {"id": f"eq.{expense_id}"}, data)
        return _to_expense(row) if row else None

    def get_distinct_years(self, calendar_id: str) -> list[int]:
        rows = self.db.select(
            "expenses",
            {"calendar_id": f"eq.{calendar_id}", "select": "year"},
        )
        return sorted(set(int(r.get("year", 0)) for r in rows) - {0})

    def delete(self, expense_id: str) -> bool:
        count = self.db.delete("expenses", {"id": f"eq.{expense_id}"})
        return count > 0

    def delete_by_year_recurring(self, calendar_id: str, year: int) -> int:
        return self.db.delete(
            "expenses",
            {"calendar_id": f"eq.{calendar_id}", "year": f"eq.{year}", "month": "eq.0"},
        )

    def delete_by_year_onetime(self, calendar_id: str, year: int) -> int:
        return self.db.delete(
            "expenses",
            {"calendar_id": f"eq.{calendar_id}", "year": f"eq.{year}", "month": "neq.0"},
        )
