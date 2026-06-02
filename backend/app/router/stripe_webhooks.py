import sys
from pathlib import Path
import traceback

import stripe
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Subscription, StripeEvent, Student, Product


sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.email_services import send_email, render_email

sys.path.append(str(Path(__file__).resolve().parents[2]))

from env import STRIPE_KEY, STRIPE_WEBHOOK_KEY, MY_EMAIL, FRONTEND_URL_PUBLIC

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
    event_data = event["data"]["object"]

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
            stripe_customer_id = event_data["customer"]
            payment_status = event_data["payment_status"]
            status = event_data["status"]
            mode = event_data["mode"]

            # DROP IN PURCHASE
            if (
                status == "complete"
                and payment_status == "paid"
                and mode == "payment"
            ):
                subscription = db.query(Subscription).filter(Subscription.stripe_customer_id == stripe_customer_id).first()

                if not subscription:
                    raise ValueError("Subscription not found")

                subscription.classes_available += 1

                db.commit()

                student = db.query(Student).filter(Student.id == subscription.student_id).first()
                product = db.query(Product).filter(Product.name == "Drop-In").first()

                dropin_purchase_body = render_email(
                        template_name="dropin_purchase.html",
                        student_name=student.first,
                        classes_available=subscription.classes_available,
                        prod_name=product.name,
                        amount=product.unit_amount,
                        title="Drop-In Purchased!",
                    )
                send_email(
                    to_email=student.email,
                    subject="Drop-In Purchased",
                    body_html=dropin_purchase_body,
                )

                dropin_purchase_body_internal = render_email(
                        template_name="dropin_purchase_internal.html",
                        id=student.id,
                        first=student.first,
                        last=student.last,
                        phone=student.phone,
                        email=student.email,
                        birthdate=student.birthdate,
                        join_date=student.created,
                        cust_id=subscription.stripe_customer_id,
                        prod_id=product.id,
                        prod_name=product.name,
                        amount=product.unit_amount,
                        classes_available=subscription.classes_available,
                        date=subscription.created,
                        title="Drop-In Purchased!",
                    )
                send_email(
                    to_email=MY_EMAIL,
                    subject="Drop-In Purchased!",
                    body_html=dropin_purchase_body_internal,
                )

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
            stripe_customer_id = event_data["customer"]
            stripe_subscription_id = event_data["id"]

            item = event_data["items"]["data"][0]

            stripe_price_id = item["price"]["id"]
            recurring = item["price"]["type"] == "recurring"
            status = event_data["status"]

            if recurring and status in ["active", "trialing"]:
                subscription = db.query(Subscription).filter(Subscription.stripe_customer_id == stripe_customer_id).first()

                if not subscription:
                    raise ValueError("Subscription not found")

                subscription.stripe_subscription_id = stripe_subscription_id
                subscription.stripe_price_id = stripe_price_id
                subscription.status = 1

                db.commit()

                student = db.query(Student).filter(Student.id == subscription.student_id).first()
                product = db.query(Product).filter(Product.price_id == subscription.stripe_price_id).first()

                new_sub_body = render_email(
                        template_name="new_sub.html",
                        student_name=student.first,
                        sub_name=product.name,
                        sub_amount=product.unit_amount,
                        title="New Subscription",
                    )
                send_email(
                    to_email=student.email,
                    subject="New Subscription",
                    body_html=new_sub_body,
                )

                new_sub_body_internal = render_email(
                        template_name="new_sub_internal.html",
                        id=student.id,
                        first=student.first,
                        last=student.last,
                        phone=student.phone,
                        email=student.email,
                        birthdate=student.birthdate,
                        join_date=student.created,
                        cust_id=subscription.stripe_customer_id,
                        prod_id=product.id,
                        prod_name=product.name,
                        sub_id=subscription.stripe_subscription_id,
                        amount=product.unit_amount,
                        date=subscription.created,
                        title="Welcome!",
                    )
                send_email(
                    to_email=MY_EMAIL,
                    subject="New Subscription!",
                    body_html=new_sub_body_internal,
                )

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
            subscription_id = event_data["id"]
            status = event_data["status"]

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