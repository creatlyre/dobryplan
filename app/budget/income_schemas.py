from __future__ import annotations

from pydantic import BaseModel, field_validator


class MonthlyHoursUpdate(BaseModel):
    year: int
    month: int
    rate_1_hours: float | None = None
    rate_2_hours: float | None = None
    rate_3_hours: float | None = None

    @field_validator("month")
    @classmethod
    def valid_month(cls, v: int) -> int:
        if not 1 <= v <= 12:
            raise ValueError("Month must be between 1 and 12")
        return v

    @field_validator("year")
    @classmethod
    def valid_year(cls, v: int) -> int:
        if not 2020 <= v <= 2100:
            raise ValueError("Year must be between 2020 and 2100")
        return v

    @field_validator("rate_1_hours", "rate_2_hours", "rate_3_hours")
    @classmethod
    def valid_hours(cls, v: float | None) -> float | None:
        if v is not None:
            if v < 0:
                raise ValueError("Hours must be non-negative")
            return round(v * 2) / 2
        return v


class MonthlyHoursResponse(BaseModel):
    id: str
    calendar_id: str
    year: int
    month: int
    rate_1_hours: float | None
    rate_2_hours: float | None
    rate_3_hours: float | None

    model_config = {"from_attributes": True}


class AdditionalEarningCreate(BaseModel):
    year: int
    month: int  # 0 = recurring (all months), 1-12 = specific month
    name: str
    amount: float

    @field_validator("month")
    @classmethod
    def valid_month(cls, v: int) -> int:
        if not 0 <= v <= 12:
            raise ValueError("Month must be between 0 and 12 (0 = recurring)")
        return v

    @field_validator("year")
    @classmethod
    def valid_year(cls, v: int) -> int:
        if not 2020 <= v <= 2100:
            raise ValueError("Year must be between 2020 and 2100")
        return v

    @field_validator("name")
    @classmethod
    def non_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name must not be empty")
        return v

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return round(v, 2)


class AdditionalEarningResponse(BaseModel):
    id: str
    calendar_id: str
    year: int
    month: int
    name: str
    amount: float

    model_config = {"from_attributes": True}
