from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, field_validator


VALID_PLANS = ("pro", "family_plus", "self_hosted")


class CheckoutRequest(BaseModel):
    plan: str
    billing_period: Literal["monthly", "annual"] = "monthly"

    @field_validator("plan")
    @classmethod
    def validate_plan(cls, v: str) -> str:
        if v not in VALID_PLANS:
            raise ValueError(f"plan must be one of {VALID_PLANS}")
        return v


class SubscriptionInfo(BaseModel):
    plan: str
    status: str
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False


class BillingEventCreate(BaseModel):
    user_id: str
    event_type: str
    plan: Optional[str] = None
    stripe_event_id: Optional[str] = None
    metadata: dict = {}
