from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator


class ExpenseCreate(BaseModel):
    year: int
    month: int  # 0 = recurring, 1-12 = specific month
    name: str
    amount: float
    recurring: bool = False

    @field_validator("year")
    @classmethod
    def valid_year(cls, v: int) -> int:
        if not 2020 <= v <= 2100:
            raise ValueError("Year must be between 2020 and 2100")
        return v

    @field_validator("month")
    @classmethod
    def valid_month(cls, v: int) -> int:
        if not 0 <= v <= 12:
            raise ValueError("Month must be between 0 and 12 (0 = recurring)")
        return v

    @field_validator("name")
    @classmethod
    def valid_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name must not be empty")
        return v

    @field_validator("amount")
    @classmethod
    def valid_amount(cls, v: float) -> float:
        if v == 0:
            raise ValueError("Amount must not be zero")
        return round(v, 2)

    @model_validator(mode="after")
    def recurring_month_consistency(self) -> "ExpenseCreate":
        if self.month == 0:
            self.recurring = True
        if self.recurring and self.month != 0:
            self.month = 0
        if self.recurring and self.amount < 0:
            raise ValueError("Recurring expenses must have positive amount")
        return self


class ExpenseUpdate(BaseModel):
    name: str | None = None
    amount: float | None = None
    month: int | None = None

    @field_validator("month")
    @classmethod
    def valid_month(cls, v: int | None) -> int | None:
        if v is not None and not 0 <= v <= 12:
            raise ValueError("Month must be between 0 and 12 (0 = recurring)")
        return v

    @field_validator("name")
    @classmethod
    def valid_name(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Name must not be empty")
        return v

    @field_validator("amount")
    @classmethod
    def valid_amount(cls, v: float | None) -> float | None:
        if v is not None:
            if v == 0:
                raise ValueError("Amount must not be zero")
            return round(v, 2)
        return v


class ExpenseResponse(BaseModel):
    id: str
    calendar_id: str
    year: int
    month: int
    name: str
    amount: float
    recurring: bool

    model_config = {"from_attributes": True}


class BulkExpenseCreate(BaseModel):
    expenses: list[ExpenseCreate]
