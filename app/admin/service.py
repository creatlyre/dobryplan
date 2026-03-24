from __future__ import annotations

from typing import Any

from app.admin.repository import AdminRepository
from app.billing.repository import BillingRepository


ALLOWED_PLANS = {"free", "pro", "family_plus"}


class AdminService:
    def __init__(self, db):
        self.admin_repo = AdminRepository(db)
        self.billing_repo = BillingRepository(db)

    def list_users(self, offset: int = 0, limit: int = 50, search: str | None = None):
        return self.admin_repo.list_users(offset, limit, search)

    def count_users(self, search: str | None = None) -> int:
        return self.admin_repo.count_users(search)

    def get_user_detail(self, user_id: str) -> dict[str, Any] | None:
        return self.admin_repo.get_user_with_subscription(user_id)

    def change_user_plan(self, user_id: str, plan: str):
        if plan not in ALLOWED_PLANS:
            raise ValueError(f"Invalid plan: {plan}. Allowed: {', '.join(sorted(ALLOWED_PLANS))}")
        return self.billing_repo.upsert_subscription(user_id=user_id, plan=plan)

    def toggle_admin(self, user_id: str, is_admin: bool):
        return self.admin_repo.update_user_admin(user_id, is_admin)

    def get_stats(self) -> dict[str, Any]:
        return {
            "user_count": self.admin_repo.count_users(),
            "plan_distribution": self.admin_repo.get_plan_distribution(),
            "recent_signups": self.admin_repo.get_recent_signups(),
        }
