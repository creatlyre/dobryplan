from __future__ import annotations

import json
import unicodedata
from pathlib import Path

from app.budget.expense_repository import ExpenseRepository
from app.budget.expense_schemas import ExpenseCreate, ExpenseUpdate
from app.database.models import Expense

_KEYWORDS_PATH = Path(__file__).parent / "category_keywords.json"


def _normalize(text: str) -> str:
    """Lowercase, strip diacritics (including Polish ł→l), collapse whitespace."""
    text = text.lower().replace("ł", "l")
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _load_keywords() -> dict[str, list[str]]:
    with open(_KEYWORDS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    # Strip _meta key — only category entries
    # Pre-normalize keywords at module load time to avoid expensive
    # unicodedata.normalize calls inside hot categorization loops.
    return {
        k: [_normalize(kw) for kw in v]
        for k, v in data.items()
        if not k.startswith("_")
    }


# Loaded once at module import
CATEGORY_KEYWORDS: dict[str, list[str]] = _load_keywords()


class ExpenseService:
    def __init__(self, repo: ExpenseRepository):
        self.repo = repo

    def get_year_data(self, calendar_id: str, year: int) -> dict:
        expenses = self.repo.get_by_calendar_year(calendar_id, year)

        recurring = []
        onetime = []
        for e in expenses:
            entry = {
                "id": e.id,
                "name": e.name,
                "amount": e.amount,
                "month": e.month,
                "recurring": e.recurring,
                "category_id": e.category_id,
            }
            if e.month == 0 or e.recurring:
                recurring.append(entry)
            else:
                onetime.append(entry)

        return {
            "year": year,
            "recurring_expenses": recurring,
            "onetime_expenses": onetime,
        }

    def create_expense(self, calendar_id: str, payload: ExpenseCreate) -> Expense:
        if not payload.category_id:
            categories = self.list_categories(calendar_id)
            detected = self._detect_category(payload.name, categories)
            if detected:
                payload.category_id = detected
        return self.repo.create(calendar_id, payload)

    def update_expense(self, expense_id: str, payload: ExpenseUpdate) -> Expense | None:
        return self.repo.update(expense_id, payload)

    def delete_expense(self, expense_id: str) -> bool:
        return self.repo.delete(expense_id)

    def bulk_create(self, calendar_id: str, items: list[ExpenseCreate]) -> list[Expense]:
        categories = None
        for item in items:
            if not item.category_id:
                if categories is None:
                    categories = self.list_categories(calendar_id)
                detected = self._detect_category(item.name, categories)
                if detected:
                    item.category_id = detected
        return [self.repo.create(calendar_id, item) for item in items]

    def delete_all_recurring(self, calendar_id: str, year: int) -> int:
        return self.repo.delete_by_year_recurring(calendar_id, year)

    def delete_all_onetime(self, calendar_id: str, year: int) -> int:
        return self.repo.delete_by_year_onetime(calendar_id, year)

    # ── Category methods ─────────────────────────────────────────────────

    def list_categories(self, calendar_id: str):
        categories = self.repo.list_categories(calendar_id)
        if not categories:
            categories = self.repo.seed_preset_categories(calendar_id)
        return categories

    def create_category(self, calendar_id: str, name: str, color: str):
        return self.repo.create_category(calendar_id, name, color)

    def get_category_breakdown(self, calendar_id: str, year: int) -> list[dict]:
        return self.repo.get_expenses_by_category(calendar_id, year)

    def _detect_category(self, name: str, categories: list) -> str | None:
        """Match expense name against keyword map, return category_id or None."""
        norm = _normalize(name)
        words = norm.split()
        cat_by_name = {c.name: c.id for c in categories}
        for cat_name, keywords in CATEGORY_KEYWORDS.items():
            if cat_name not in cat_by_name:
                continue
            for norm_kw in keywords:
                for w in words:
                    if norm_kw in w or (len(w) >= 3 and w in norm_kw):
                        return cat_by_name[cat_name]
        return None

    def auto_categorize(self, calendar_id: str, year: int) -> dict:
        """Auto-assign categories to uncategorized expenses for a year. Returns count of updated."""
        categories = self.list_categories(calendar_id)
        expenses = self.repo.get_by_calendar_year(calendar_id, year)
        uncategorized = [e for e in expenses if not e.category_id]

        updated = 0
        for e in uncategorized:
            cat_id = self._detect_category(e.name, categories)
            if cat_id:
                from app.budget.expense_schemas import ExpenseUpdate
                self.repo.update(e.id, ExpenseUpdate(category_id=cat_id))
                updated += 1

        return {"total": len(uncategorized), "updated": updated}
