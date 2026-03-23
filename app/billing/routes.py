from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.auth.dependencies import get_current_user
from app.billing.repository import BillingRepository
from app.billing.schemas import CheckoutRequest
from app.billing.service import BillingService
from app.database.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])


def _get_billing_service(db=Depends(get_db)) -> BillingService:
    return BillingService(BillingRepository(db))


@router.post("/checkout")
async def create_checkout(
    body: CheckoutRequest,
    request: Request,
    user=Depends(get_current_user),
    service: BillingService = Depends(_get_billing_service),
):
    base_url = str(request.base_url).rstrip("/")

    if body.plan == "self_hosted":
        success_url = f"{base_url}/pricing?purchased=true"
        cancel_url = f"{base_url}/pricing"
    else:
        success_url = f"{base_url}/billing/settings?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{base_url}/billing/settings"

    try:
        checkout_url = service.create_checkout_session(
            user_id=user.id,
            email=user.email,
            plan=body.plan,
            success_url=success_url,
            cancel_url=cancel_url,
            billing_period=body.billing_period,
        )
        return JSONResponse({"url": checkout_url})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Failed to create checkout session")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    db = next(get_db())
    service = BillingService(BillingRepository(db))

    try:
        service.handle_webhook_event(payload, sig_header)
    except Exception as e:
        logger.exception("Webhook processing error: %s", e)
        raise HTTPException(status_code=400, detail="Webhook verification failed")

    return JSONResponse({"status": "ok"})


@router.post("/portal")
async def create_portal(
    request: Request,
    user=Depends(get_current_user),
    service: BillingService = Depends(_get_billing_service),
):
    db = next(get_db())
    repo = BillingRepository(db)
    sub = repo.get_subscription(user.id)

    if not sub or not sub.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found")

    base_url = str(request.base_url).rstrip("/")
    return_url = f"{base_url}/billing/settings"

    try:
        portal_url = service.create_portal_session(sub.stripe_customer_id, return_url)
        return JSONResponse({"url": portal_url})
    except Exception:
        logger.exception("Failed to create portal session")
        raise HTTPException(status_code=500, detail="Failed to create portal session")
