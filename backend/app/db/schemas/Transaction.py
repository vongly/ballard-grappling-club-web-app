from pydantic import BaseModel
from datetime import date, datetime


class Create(BaseModel):
    student_id: int
    product_id: int

    stripe_checkout_session_id: str
    stripe_payment_intent_id: str | None = None
    stripe_invoice_id: str | None = None

    amount_total: int
    currency: str
    price_id: str
    type: str
    status: str
    raw_session: dict

class Update(BaseModel):
    student_id: int | None = None
    product_id: int | None = None

    stripe_checkout_session_id: str | None = None
    stripe_payment_intent_id: str | None = None
    stripe_invoice_id: str | None = None

    amount_total: int | None = None
    currency: str | None = None
    price_id: str | None = None
    type: str | None = None
    status: str | None = None
    raw_session: dict

class Out(BaseModel):
    student_id: int | None = None
    product_id: int | None = None

    stripe_checkout_session_id: str | None = None
    stripe_payment_intent_id: str | None = None
    stripe_invoice_id: str | None = None

    amount_total: int | None = None
    currency: str | None = None
    price_id: str | None = None
    type: str | None = None
    status: str | None = None
    raw_session: dict

    created: datetime
    updated: datetime

    class Config:
        from_attributes = True