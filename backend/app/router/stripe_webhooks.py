import sys
from pathlib import Path
import traceback

import stripe
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Subscription, StripeEvent

sys.path.append(str(Path(__file__).resolve().parents[2]))

from env import STRIPE_KEY, STRIPE_WEBHOOK_KEY

router = APIRouter()
stripe.api_key = STRIPE_KEY


# =========================================================
# IDEMPOTENCY GUARD
# =========================================================
def acquire_event_lock(db: Session, event_id: str) -> bool:
    existing = (
        db.query(StripeEvent)
        .filter(StripeEvent.event_id == event_id)
        .first()
    )

    if existing:
        return False

    db.add(StripeEvent(event_id=event_id, status=0))
    db.commit()
    return True


# =========================================================
# WEBHOOK
# =========================================================
@router.post("")
async def update_subscription(
    request: Request,
    db: Session = Depends(get_db),
):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    print("\n🔥 WEBHOOK HIT")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=STRIPE_WEBHOOK_KEY,
        )
    except Exception as e:
        print("❌ Signature verification failed:", str(e))
        raise HTTPException(status_code=400, detail=str(e))

    event_type = event["type"]
    event_id = event["id"]

    # IMPORTANT: StripeObject (NOT dict)
    data = event["data"]["object"]

    print("📩 Event:", event_type)

    # =========================================================
    # IDEMPOTENCY
    # =========================================================
    if not acquire_event_lock(db, event_id):
        print(f"⚠️ Duplicate event ignored: {event_id}")
        return {"status": "already_processed"}

    # =========================================================
    # IGNORE UNSUPPORTED EVENTS
    # =========================================================
    if event_type not in [
        "checkout.session.completed",
        "customer.subscription.created",
        "customer.subscription.deleted",
        "customer.subscription.updated",
    ]:
        db.query(StripeEvent).filter(
            StripeEvent.event_id == event_id
        ).update({"status": 1})
        db.commit()

        return {"status": "ignored"}

    # =========================================================
    # CHECKOUT SESSION COMPLETED
    # =========================================================
    if event_type == "checkout.session.completed":
        try:
            stripe_customer_id = data["customer"]
            payment_status = data["payment_status"]
            status = data["status"]
            mode = data["mode"]

            # FIX: DO NOT use .get() on StripeObject
            if (
                status == "complete"
                and payment_status == "paid"
                and mode == "payment"
            ):
                subscription = (
                    db.query(Subscription)
                    .filter(
                        Subscription.stripe_customer_id == stripe_customer_id
                    )
                    .first()
                )

                if not subscription:
                    raise ValueError("Subscription not found")

                subscription.classes_available += 1

            db.commit()

            return {
                "status": "success",
                "transaction": "one time purchase",
            }

        except Exception:
            db.rollback()

            print("\n🔥 WEBHOOK ERROR")
            print(traceback.format_exc())

            raise HTTPException(status_code=500, detail="Checkout failed")

    # =========================================================
    # SUBSCRIPTION CREATED
    # =========================================================
    if event_type == "customer.subscription.created":
        try:
            stripe_customer_id = data["customer"]
            stripe_subscription_id = data["id"]

            item = data["items"]["data"][0]

            stripe_price_id = item["price"]["id"]
            recurring = item["price"]["type"] == "recurring"
            status = data["status"]

            if recurring and status in ["active", "trialing"]:

                subscription = (
                    db.query(Subscription)
                    .filter(
                        Subscription.stripe_customer_id == stripe_customer_id
                    )
                    .first()
                )

                if not subscription:
                    raise ValueError("Subscription not found")

                subscription.stripe_subscription_id = stripe_subscription_id
                subscription.stripe_price_id = stripe_price_id
                subscription.status = 1

                db.commit()

            return {
                "status": "success",
                "transaction": "subscription created",
            }

        except Exception:
            db.rollback()

            print("\n🔥 WEBHOOK ERROR")
            print(traceback.format_exc())

            raise HTTPException(status_code=500, detail="Subscription create failed")

    # =========================================================
    # SUBSCRIPTION UPDATED
    # =========================================================
    if event_type == "customer.subscription.updated":
        try:
            db.commit()
            return {"status": "success", "transaction": "subscription updated"}

        except Exception:
            db.rollback()

            print("\n🔥 WEBHOOK ERROR")
            print(traceback.format_exc())

            raise HTTPException(status_code=500, detail="Subscription update failed")

    # =========================================================
    # SUBSCRIPTION DELETED
    # =========================================================
    if event_type == "customer.subscription.deleted":
        try:
            subscription_id = data["id"]
            status = data["status"]

            if status == "canceled":
                subscription = (
                    db.query(Subscription)
                    .filter(
                        Subscription.stripe_subscription_id == subscription_id
                    )
                    .first()
                )

                if not subscription:
                    raise ValueError("Subscription not found")

                subscription.status = 3

                db.commit()

            return {
                "status": "success",
                "transaction": "subscription deleted",
            }

        except Exception:
            db.rollback()

            print("\n🔥 WEBHOOK ERROR")
            print(traceback.format_exc())

            raise HTTPException(status_code=500, detail="Subscription delete failed")