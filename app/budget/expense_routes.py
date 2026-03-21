from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user
from app.budget.expense_repository import ExpenseRepository
from app.budget.expense_schemas import BulkExpenseCreate, ExpenseCreate, ExpenseResponse, ExpenseUpdate
from app.budget.expense_service import ExpenseService
from app.database.database import get_db

router = APIRouter(prefix="/api/budget/expenses", tags=["expenses"])


def _service(db) -> ExpenseService:
    return ExpenseService(ExpenseRepository(db))


@router.get("")
async def get_expenses(year: int, user=Depends(get_current_user), db=Depends(get_db)):
    if not user.calendar_id:
        raise HTTPException(status_code=400, detail="No calendar linked")
    service = _service(db)
    data = service.get_year_data(user.calendar_id, year)
    return {"data": data}


@router.post("")
async def create_expense(
    payload: ExpenseCreate,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    if not user.calendar_id:
        raise HTTPException(status_code=400, detail="No calendar linked")
    service = _service(db)
    expense = service.create_expense(user.calendar_id, payload)
    return {"data": ExpenseResponse.model_validate(expense, from_attributes=True).model_dump()}


@router.post("/bulk")
async def bulk_create_expenses(
    payload: BulkExpenseCreate,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    if not user.calendar_id:
        raise HTTPException(status_code=400, detail="No calendar linked")
    service = _service(db)
    expenses = service.bulk_create(user.calendar_id, payload.expenses)
    return {"data": [ExpenseResponse.model_validate(e, from_attributes=True).model_dump() for e in expenses]}


@router.put("/{expense_id}")
async def update_expense(
    expense_id: str,
    payload: ExpenseUpdate,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = _service(db)
    expense = service.update_expense(expense_id, payload)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"data": ExpenseResponse.model_validate(expense, from_attributes=True).model_dump()}


@router.delete("/bulk")
async def bulk_delete_expenses(
    year: int,
    type: str = "recurring",
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    if not user.calendar_id:
        raise HTTPException(status_code=400, detail="No calendar linked")
    service = _service(db)
    if type == "recurring":
        count = service.delete_all_recurring(user.calendar_id, year)
    else:
        count = service.delete_all_onetime(user.calendar_id, year)
    return {"ok": True, "deleted": count}


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: str,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = _service(db)
    deleted = service.delete_expense(expense_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"ok": True}
