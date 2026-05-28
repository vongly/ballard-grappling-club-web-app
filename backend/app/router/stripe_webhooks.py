import sys
from pathlib import Path
import traceback

import stripe
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from db.database import get_db, SessionLocal
from db.models import Transaction, Subscription, Student, StripeEvent

sys.path.append(str(Path(__file__).resolve().parents[2]))

from env import STRIPE_KEY, STRIPE_WEBHOOK_KEY

router = APIRouter()

stripe.api_key = STRIPE_KEY

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

    print("📩 Event:", event_type)

    if event_type not in [
        "checkout.session.completed",
        "customer.subscription.created",
        "customer.subscription.deleted",
        "customer.subscription.updated",
    ]:
        print("ℹ️ Ignored event")
        return {"status": "ignored"}

    elif event_type == "checkout.session.completed":
        data = event["data"]["object"]

        try:
            stripe_customer_id = data["customer"]

            payment_status = data["payment_status"]
            status = data["status"]
            mode = data["mode"]

            if status == 'complete' and payment_status == 'paid' and mode == "payment":
                subscription = (db.query(Subscription).filter(Subscription.stripe_customer_id == stripe_customer_id).first())
                subscription.classes_available = subscription.classes_available + 1

                db.commit()

            return {
                "status": "success",
                'transaction': 'one time purchase',
            }

        except Exception as e:

            db.rollback()

            print("\n🔥 WEBHOOK ERROR")
            print("Type:", type(e))
            print("Error:", repr(e))
            print("Traceback:\n", traceback.format_exc())

            raise HTTPException(
                status_code=500,
                detail=str(e),
            )

    elif event_type == "customer.subscription.created":
        data = event["data"]["object"]

        try:

            stripe_customer_id = data["customer"]
            stripe_subscription_id = data["id"]

            item = data["items"]["data"][0]
            amount = item["plan"]["amount"]
            stripe_price_id = item["price"]["id"]
            recurring = 1 if item["price"]["type"] == "recurring" else 0
            status = data["status"]

            if status == 'active' and recurring == 1:
                subscription = (db.query(Subscription).filter(Subscription.stripe_customer_id == stripe_customer_id).first())

                subscription.stripe_subscription_id = stripe_subscription_id
                subscription.stripe_price_id = stripe_price_id
                subscription.status = 1

                db.commit()

            return {
                "status": "success",
                'transaction': 'subscription created',
            }

        except Exception as e:

            db.rollback()

            print("\n🔥 WEBHOOK ERROR")
            print("Type:", type(e))
            print("Error:", repr(e))
            print("Traceback:\n", traceback.format_exc())

            raise HTTPException(
                status_code=500,
                detail=str(e),
            )

    elif event["type"] == "customer.subscription.updated":
        data = event["data"]["object"]
        
        #print(data)
        pass

        '''
        Logic when a request to cancel occurs
        -> need to understand the combination of {data} field values

        subscription.status = 2 # 2 -> Request to Canceled
        '''



    elif event_type == "customer.subscription.deleted":
        data = event["data"]["object"]
        try:
            subscription_id = data["id"]
            status = data["status"]

            subscription_data = {
                "subscription_id": subscription_id,
                "status": status,
            }

            if status == 'canceled':
                subscription = (db.query(Subscription).filter(Subscription.stripe_subscription_id == subscription_id).first())

                subscription.status = 3 # 3 -> Canceled

                db.commit()

            return {
                "status": "success",
                'transaction': 'subscription deleted',
                "data": subscription_data,
                "status": status,
            }

        except Exception as e:

            db.rollback()

            print("\n🔥 WEBHOOK ERROR")
            print("Type:", type(e))
            print("Error:", repr(e))
            print("Traceback:\n", traceback.format_exc())

            raise HTTPException(
                status_code=500,
                detail=str(e),
            )
        
