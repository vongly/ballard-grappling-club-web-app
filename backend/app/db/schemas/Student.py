from pydantic import BaseModel
from datetime import date, datetime


class Create(BaseModel):
    first: str
    last: str
    password: str
    phone: str
    email: str | None = None
    birthdate: date

    address_1: str
    address_2: str | None = None
    city: str
    state: str
    zipcode: str

    photo_url: str | None = None
    waiver_url: str | None = None

    emergency_contact_name: str
    emergency_contact_relationship: str
    emergency_contact_phone: str
    type: int = 1

class Update(BaseModel):
    first: str | None = None
    last: str | None = None
    phone: str | None = None
    email: str | None = None
    birthdate: date | None = None

    address_1: str | None = None
    address_2: str | None = None
    city: str | None = None
    state: str | None = None
    zipcode: str | None = None

    photo_url: str | None = None
    waiver_url: str | None = None

    stripe_cust_id: str | None

    emergency_contact_name: str | None = None
    emergency_contact_relationship: str | None = None
    emergency_contact_phone: str | None = None

    type: int | None = None
    trial_initiated: date | None = None

class Out(BaseModel):
    id: int
    first: str
    last: str
    phone: str
    email: str | None
    birthdate: date

    address_1: str
    address_2: str | None
    city: str
    state: str
    zipcode: str

    photo_url: str | None
    waiver_url: str | None = None

    stripe_cust_id: str | None

    emergency_contact_name: str
    emergency_contact_relationship: str
    emergency_contact_phone: str

    type: int
    trial_initiated: date
    created: datetime
    updated: datetime

    class Config:
        from_attributes = True