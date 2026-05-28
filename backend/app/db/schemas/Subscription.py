from pydantic import BaseModel
from datetime import date, datetime


class Create(BaseModel):
    stripe_customer_id: str
    stripe_subscription_id: str | None = None
    stripe_price_id: str | None = None
    status: int
    # 0 -> active
    # 1 -> canceled
    # 2 -> past_due
    # 4 -> unpaid
    classes_available: int

class Update(BaseModel):
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    stripe_price_id: str | None = None
    status: int | None = None
    classes_available: int | None = None

class Out(BaseModel):
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    stripe_price_id: str | None = None
    status: int | None = None
    classes_available: int | None = None

    created: datetime
    updated: datetime

    class Config:
        from_attributes = True