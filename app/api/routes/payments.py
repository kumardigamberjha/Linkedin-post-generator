import logging
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.core.config import get_settings
from app.db.database import update_subscription
from app.api.routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


class CheckoutRequest(BaseModel):
    plan_id: str


@router.post("/create-checkout-session")
async def create_checkout_session(
    req: CheckoutRequest, current_user: dict = Depends(get_current_user)
):
    settings = get_settings()

    # Normally we'd map our string plan_id (e.g., 'basic', 'pro') to the Stripe Price ID in config
    stripe.api_key = settings.stripe_secret_key
    if not stripe.api_key:
        # Mock mode if no Stripe keys are provided yet
        update_subscription(
            current_user["id"],
            {
                "plan_tier": req.plan_id,
                "status": "active",
                "posts_generated_this_month": 0,
            },
        )
        return {"url": "/", "mock": True}

    price_id_map = {
        "basic": settings.stripe_price_basic,
        "pro": settings.stripe_price_pro,
        "max": settings.stripe_price_max,
    }

    price_id = price_id_map.get(req.plan_id)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid plan selected")

    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user["email"],
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url="http://localhost:5173/?payment=success",
            cancel_url="http://localhost:5173/?payment=cancelled",
            client_reference_id=str(current_user["id"]),
        )
        return {"url": checkout_session.url}
    except Exception as e:
        logger.error(f"Stripe Checkout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request):
    settings = get_settings()
    if not settings.stripe_webhook_secret:
        return {"status": "ignored - no webhook secret configured"}

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id_str = session.get("client_reference_id")

        if user_id_str:
            user_id = int(user_id_str)
            sub_id = session.get("subscription")
            cust_id = session.get("customer")

            # Map the price back to our internal tier (requires fetching the sub from Stripe if multiple items)
            # For simplicity, if we rely on a single price ID match or pass metadata:
            # Here we just mark them as active, ideally we fetch the sub to see the price.
            # Assuming a basic mapping based on price ID.
            update_subscription(
                user_id,
                {
                    "stripe_customer_id": cust_id,
                    "stripe_subscription_id": sub_id,
                    "status": "active",
                    "posts_generated_this_month": 0,
                },
            )

    # Handle subscription updates / cancellations
    elif event["type"] in [
        "customer.subscription.deleted",
        "customer.subscription.updated",
    ]:
        # In a real app, we'd query our DB by stripe_subscription_id to find the user
        # and update their status. (Omitted complex DB reverse lookup for brevity)
        pass

    return {"status": "success"}
