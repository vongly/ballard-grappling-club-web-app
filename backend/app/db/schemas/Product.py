from pydantic import BaseModel
from datetime import date, datetime


class Create(BaseModel):
    product_id: str
    name: str
    description: str | None = None
    currency: str
    price_id: str
    recurring: int
    unit_amount: int
    active: int
    product_order: int
    upgrade: int
    subscription_classes_per_week: int

class Update(BaseModel):
    product_id: str | None = None
    name: str | None = None
    description: str | None = None
    currency: str | None = None
    price_id: str | None = None
    recurring: int | None = None
    unit_amount: int | None = None
    active: int | None = None
    product_order: int | None = None
    upgrade: int | None = None
    subscription_classes_per_week: int | None = None

class Out(BaseModel):
    product_id: str | None = None
    name: str | None = None
    description: str | None = None
    currency: str | None = None
    price_id: str | None = None
    recurring: int | None = None
    unit_amount: int | None = None
    active: int | None = None
    product_order: int | None = None
    upgrade: int | None = None
    subscription_classes_per_week: int | None = None

    created: datetime
    updated: datetime

    class Config:
        from_attributes = True