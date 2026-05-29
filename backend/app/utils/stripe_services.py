import sys
from pathlib import Path
from datetime import datetime, date, timedelta, timezone
from dateutil.relativedelta import relativedelta

import stripe
from sqlalchemy.dialects.postgresql import insert
from typing import Optional, Dict, Any

sys.path.append(str(Path(__file__).resolve().parents[1]))

from db.models import Student, Product, Subscription
from db.database import SessionLocal

sys.path.append(str(Path(__file__).resolve().parents[2]))

from env import STRIPE_KEY, FRONTEND_URL, TRIAL_LENGTH

# times in utc
now = datetime.now()
FIRST_DAY_NEXT_MONTH = (
    now.replace(day=1, hour=10) + relativedelta(months=1)
)
LAUNCH_TIMESTAMP = datetime(2026, 6, 1, 11, 0, 0)


class StripeServices:
    def __init__(self, api_key: str, db):
        stripe.api_key = api_key
        self.db = db

    def get_products(self):
        product_obj = stripe.Product.list(active=True)

        products = []

        for product in product_obj.data:
            prices = stripe.Price.list(
                product=product.id,
                active=True
            )

            details = {
                "product_id": product.id,
                "name": product.name,
                "description": product.description,
                "active": 1 if product.active else 0,
                "prices": [
                    {
                        "price_id": price.id,
                        "unit_amount": price.unit_amount,
                        "currency": price.currency,
                        "recurring": 1 if price.recurring else 0,
                    }
                    for price in prices.data
                ]
            }
            price = details.pop('prices')[0]
            details.update(price)
            products.append(details)

        return products

    def sync_products(self):
        products = self.get_products()

        for p in products:
            # Merges Stripe products with db
            product_stmt = (
                insert(Product)
                .values(
                    product_id=p["product_id"],
                    name=p["name"],
                    description=p.get("description"),
                    currency=p["currency"],
                    price_id=p["price_id"],
                    recurring=bool(p["recurring"]),
                    unit_amount=p["unit_amount"],
                    active=bool(p["active"]),
                )
                .on_conflict_do_update(
                    index_elements=[Product.product_id],
                    set_={
                        "name": p["name"],
                        "description": p.get("description"),
                        "currency": p["currency"],
                        "price_id": p["price_id"],
                        "recurring": bool(p["recurring"]),
                        "unit_amount": p["unit_amount"],
                        "active": bool(p["active"]),
                    },
                )
                .returning(Product.id)
            )

            self.db.execute(product_stmt)

        self.db.commit()

        return {
            "status": "success",
            "synced_count": len(products)
        }

    def get_student(self, student_id: str):

        student = self.db.query(Student).filter(Student.id == student_id).first()

        return student


    def get_or_create_customer(self, student_id):
        student = (self.db.query(Student).filter(Student.id == student_id).first())
        if not student:
            raise Exception("Student not found")

        subscription = (self.db.query(Subscription).filter(Subscription.student_id == student.id).first())
        customer = None

        if subscription and subscription.stripe_customer_id:
            customer = stripe.Customer.retrieve(subscription.stripe_customer_id)

        else:
            customer = stripe.Customer.create(email=student.email,metadata={"student_id": str(student.id)})

            if subscription:
                subscription.stripe_customer_id = customer.id
            else:
                subscription = Subscription(student_id=student.id,stripe_customer_id=customer.id,stripe_price_id=None)
                self.db.add(subscription)

            self.db.commit()
            self.db.refresh(subscription)
        return customer

    def create_checkout(self, student_id: int, product_id: int, frontend_url: str, first_day_next_month=FIRST_DAY_NEXT_MONTH, launch_timestamp=LAUNCH_TIMESTAMP):

        student = self.db.query(Student).filter(Student.id == student_id).first()
        product = self.db.query(Product).filter(Product.id == product_id).first()

        if not student:
            raise Exception("Student not found")

        if not product:
            raise Exception("Product not found")

        # 1. Get or create Stripe customer
        customer = self.get_or_create_customer(student_id)
        customer_id = customer.id

        # 2. Determine mode
        mode = "subscription" if product.recurring else "payment"

        checkout_data = {
            "mode": mode,
            "customer": customer_id,
            "payment_method_types": ["card"],
            "line_items": [
                {
                    "price": product.price_id,
                    "quantity": 1,
                }
            ],
            "success_url": f"{frontend_url}/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{frontend_url}/cancel",
        }


        # 3. ONLY add subscription_data if needed (optional)
        if mode == "subscription" and first_day_next_month and launch_timestamp:
            if now < LAUNCH_TIMESTAMP:
                # PRE-LAUNCH: no billing until launch
                checkout_data["subscription_data"] = {
                    "trial_end": int(LAUNCH_TIMESTAMP.timestamp())
                }
            else:
                # POST-LAUNCH: normal billing - no trial
                checkout_data["subscription_data"] = {
                    "billing_cycle_anchor": first_day_next_month,
                    "proration_behavior": "create_prorations"
                }

        session = stripe.checkout.Session.create(**checkout_data)

        return session

    def eligble_for_class(self, student_id: int, trial_length=TRIAL_LENGTH):
        student = self.db.query(Student).filter(Student.id == student_id).first()
        existing_customer_id = student.stripe_cust_id

        # Check for Trial Eligibility
        if not student.trial_initiated:
            student.trial_initiated = date.today()
            return True
        elif date.today() < student.triail_initiated + timedelta(days=trial_length):
            return True
        elif date.today() >= student.triail_initiated + timedelta(days=trial_length):
            pass
        elif not existing_customer_id:
            False


        customer = self.get_or_create_customer(student.email)

        # Check for Drop In -> Daily Pass

        # Check for Subscription
            # Check for 1 Day/Week subscription
            # Check Unlimited

        pass


if __name__ == '__main__':
    stripe_call = StripeServices(api_key=STRIPE_KEY, db=SessionLocal())
    stripe_call.sync_products()
