from pydantic import BaseModel
from datetime import datetime, date, time

#
class Create(BaseModel):
    name: str
    class_date: date
    class_time: time
    type: int = 1

class Update(BaseModel):
    class_date: date | None = None
    class_time: time | None = None
    type: int | None = None

class Out(BaseModel):
    id: int
    class_date: date
    class_time: time
    type: int = 1
    created: datetime
    updated: datetime

    class Config:
        from_attributes = True