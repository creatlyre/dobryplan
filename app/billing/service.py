from __future__ import annotations

import logging
from datetime import datetime, timezone

import stripe

from app.billing.repository import BillingRepository
from config import Settings

logger = logging.getLogger(__name__)

settings = Settings()

stripe.api_key = settings.STRIPE_SECRET_KEY

PLAN_PRICE_MAP = {
    "pro": settings.STRIPE_PRO_PRICE_ID,
    "family_plus": settings.STRIPE_FAMILY_PLUS_PRICE_ID,
}


class BillingService:
    def __init__(self, repo: BillingRepository):
        self.repo = repo

    def create_checkout_session(
        self,
        user_id: str,
        email: str,
        plan: str,
        success_url: str,
        cancel_url: str,
    ) -> str:
        price_id = PLAN_PRICE_MAP.get(plan)
        if not price_id:
            raise ValueError(f"No Stripe price configured for plan: {plan}")

        # Get or create Stripe customer
        sub = self.repo.get_subscription(user_id)
        stripe_customer_id = sub.stripe_customer_id if sub else None

        if not stripe_customer_id:
            customer = stripe.Customer.create(email=email, metadata={"user_id": user_id})
            stripe_customer_id = customer.id
            self.repo.upsert_subscription(
                user_id=user_id,
                stripe_customer_id=stripe_customer_id,
                plan="free",
                status="active",
            )

        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=stripe_customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": user_id, "plan": plan},
        )
        return session.url

    def create_portal_session(self, stripe_customer_id: str, return_url: str) -> str:
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=return_url,
        )
        return session.url

    def handle_webhook_event(self, payload: bytes, sig_header: str) -> None:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )

        event_type = event["type"]
        data_object = event["data"]["object"]

        if event_type == "checkout.session.completed":
            self._handle_checkout_completed(event, data_object)
        elif event_type == "customer.subscription.updated":
            self._handle_subscription_updated(event, data_object)
        elif event_type == "customer.subscription.deleted":
            self._handle_subscription_deleted(event, data_object)
        elif event_type == "invoice.payment_failed":
            self._handle_payment_failed(event, data_object)
        else:
            logger.info("Unhandled Stripe event type: %s", event_type)

    def _resolve_user_id(self, data_object: dict) -> str | None:
        metadata = data_object.get("metadata") or {}
        user_id = metadata.get("user_id")
        if user_id:
            return user_id

        customer_id = data_object.get("customer")
        if customer_id:
            sub = self.repo.get_subscription_by_stripe_customer(customer_id)
            if sub:
                return sub.user_id
        return None

    def _handle_checkout_completed(self, event: dict, session: dict) -> None:
        metadata = session.get("metadata") or {}
        user_id = metadata.get("user_id")
        plan = metadata.get("plan", "pro")
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")

        if not user_id:
            logger.warning("checkout.session.completed without user_id in metadata")
            return

        self.repo.upsert_subscription(
            user_id=user_id,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            plan=plan,
            status="active",
        )
        self.repo.log_billing_event(
            user_id=user_id,
            event_type="subscribe",
            plan=plan,
            stripe_event_id=event.get("id"),
            metadata={"session_id": session.get("id")},
        )

    def _handle_subscription_updated(self, event: dict, subscription: dict) -> None:
        customer_id = subscription.get("customer")
        user_id = self._resolve_user_id(subscription)
        if not user_id:
            logger.warning("subscription.updated: cannot resolve user_id for customer %s", customer_id)
            return

        # Determine plan from price
        items = subscription.get("items", {}).get("data", [])
        new_plan = None
        if items:
            price_id = items[0].get("price", {}).get("id")
            for plan_key, pid in PLAN_PRICE_MAP.items():
                if pid == price_id:
                    new_plan = plan_key
                    break

        existing = self.repo.get_subscription(user_id)
        old_plan = existing.plan if existing else "free"

        period_end_ts = subscription.get("current_period_end")
        period_end = datetime.fromtimestamp(period_end_ts, tz=timezone.utc) if period_end_ts else None

        status_map = {
            "active": "active",
            "past_due": "past_due",
            "canceled": "canceled",
            "incomplete": "incomplete",
        }
        stripe_status = subscription.get("status", "active")
        mapped_status = status_map.get(stripe_status, "active")

        self.repo.upsert_subscription(
            user_id=user_id,
            stripe_customer_id=customer_id,
            plan=new_plan or old_plan,
            status=mapped_status,
            current_period_end=period_end,
            cancel_at_period_end=bool(subscription.get("cancel_at_period_end", False)),
        )

        if new_plan and new_plan != old_plan:
            self.repo.log_billing_event(
                user_id=user_id,
                event_type="plan_change",
                plan=new_plan,
                stripe_event_id=event.get("id"),
                metadata={"old_plan": old_plan, "new_plan": new_plan},
            )

    def _handle_subscription_deleted(self, event: dict, subscription: dict) -> None:
        user_id = self._resolve_user_id(subscription)
        if not user_id:
            logger.warning("subscription.deleted: cannot resolve user_id")
            return

        existing = self.repo.get_subscription(user_id)
        self.repo.upsert_subscription(
            user_id=user_id,
            plan=existing.plan if existing else "free",
            status="canceled",
        )
        self.repo.log_billing_event(
            user_id=user_id,
            event_type="churn",
            plan=existing.plan if existing else None,
            stripe_event_id=event.get("id"),
        )

    def _handle_payment_failed(self, event: dict, invoice: dict) -> None:
        customer_id = invoice.get("customer")
        sub = self.repo.get_subscription_by_stripe_customer(customer_id) if customer_id else None
        if not sub:
            logger.warning("invoice.payment_failed: cannot find subscription for customer %s", customer_id)
            return

        self.repo.upsert_subscription(
            user_id=sub.user_id,
            plan=sub.plan,
            status="past_due",
        )
        self.repo.log_billing_event(
            user_id=sub.user_id,
            event_type="payment_failed",
            plan=sub.plan,
            stripe_event_id=event.get("id"),
            metadata={"invoice_id": invoice.get("id")},
        )
