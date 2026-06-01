from pydantic import BaseModel
from datetime import datetime, date, time, datetime

#
class Create(BaseModel):
    name: str
    class_datetime: datetime
    duration: int
    type: int = 0
    promotion: int = 0

class Update(BaseModel):
    name: str | None = None
    class_datetime: datetime | None = None
    duration: int
    type: int | None = None
    promotion: int | None = None

class Out(BaseModel):
    id: int
    name: str
    class_datetime: datetime
    duration: int
    type: int
    promotion: int
    created: datetime
    updated: datetime

    class Config:
        from_attributes = True