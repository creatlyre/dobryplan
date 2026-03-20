from __future__ import annotations

from app.budget.expense_repository import ExpenseRepository
from app.budget.expense_schemas import ExpenseCreate, ExpenseUpdate
from app.database.models import Expense


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
        return self.repo.create(calendar_id, payload)

    def update_expense(self, expense_id: str, payload: ExpenseUpdate) -> Expense | None:
        return self.repo.update(expense_id, payload)

    def delete_expense(self, expense_id: str) -> bool:
        return self.repo.delete(expense_id)

    def bulk_create(self, calendar_id: str, items: list[ExpenseCreate]) -> list[Expense]:
        return [self.repo.create(calendar_id, item) for item in items]
