from __future__ import annotations

from datetime import datetime, timezone

from app.database.models import Expense, ExpenseCategory
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
        category_id=row.get("category_id"),
        created_at=_parse_dt(row.get("created_at")),
        updated_at=_parse_dt(row.get("updated_at")),
    )


def _to_category(row: dict) -> ExpenseCategory:
    return ExpenseCategory(
        id=row.get("id", ""),
        calendar_id=row.get("calendar_id", ""),
        name=row.get("name", ""),
        color=row.get("color", "#6366f1"),
        is_preset=bool(row.get("is_preset", False)),
        sort_order=int(row.get("sort_order", 0)),
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
        data = {
            "calendar_id": calendar_id,
            "year": payload.year,
            "month": payload.month,
            "name": payload.name,
            "amount": payload.amount,
            "recurring": payload.recurring,
        }
        if payload.category_id is not None:
            data["category_id"] = payload.category_id
        row = self.db.insert("expenses", data)
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
        if payload.category_id is not None:
            data["category_id"] = payload.category_id
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

    # ── Category methods ─────────────────────────────────────────────────

    _PRESET_CATEGORIES = [
        {"name": "Groceries", "color": "#10b981", "sort_order": 1},
        {"name": "Rent", "color": "#6366f1", "sort_order": 2},
        {"name": "Utilities", "color": "#06b6d4", "sort_order": 3},
        {"name": "Transport", "color": "#f59e0b", "sort_order": 4},
        {"name": "Entertainment", "color": "#ec4899", "sort_order": 5},
        {"name": "Health", "color": "#ef4444", "sort_order": 6},
        {"name": "Education", "color": "#8b5cf6", "sort_order": 7},
        {"name": "Other", "color": "#64748b", "sort_order": 8},
    ]

    def list_categories(self, calendar_id: str) -> list[ExpenseCategory]:
        rows = self.db.select(
            "expense_categories",
            {"calendar_id": f"eq.{calendar_id}", "order": "sort_order.asc"},
        )
        return [_to_category(row) for row in rows]

    def create_category(self, calendar_id: str, name: str, color: str) -> ExpenseCategory:
        row = self.db.insert(
            "expense_categories",
            {
                "calendar_id": calendar_id,
                "name": name,
                "color": color,
                "is_preset": False,
                "sort_order": 100,
            },
        )
        return _to_category(row)

    def seed_preset_categories(self, calendar_id: str) -> list[ExpenseCategory]:
        results: list[ExpenseCategory] = []
        for preset in self._PRESET_CATEGORIES:
            row = self.db.insert(
                "expense_categories",
                {
                    "calendar_id": calendar_id,
                    "name": preset["name"],
                    "color": preset["color"],
                    "is_preset": True,
                    "sort_order": preset["sort_order"],
                },
            )
            results.append(_to_category(row))
        return results

    def get_expenses_by_category(self, calendar_id: str, year: int) -> list[dict]:
        expenses = self.get_by_calendar_year(calendar_id, year)
        categories = self.list_categories(calendar_id)
        cat_map = {c.id: c for c in categories}

        # Aggregate by category_id
        buckets: dict[str | None, dict] = {}
        for e in expenses:
            cid = e.category_id
            if cid not in buckets:
                cat = cat_map.get(cid) if cid else None
                buckets[cid] = {
                    "category_id": cid,
                    "category_name": cat.name if cat else None,
                    "color": cat.color if cat else None,
                    "total_amount": 0.0,
                    "count": 0,
                }
            buckets[cid]["total_amount"] += e.amount
            buckets[cid]["count"] += 1

        return sorted(buckets.values(), key=lambda b: b["total_amount"], reverse=True)
