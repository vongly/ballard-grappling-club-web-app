from pydantic import BaseModel
from datetime import datetime

#
class Create(BaseModel):
    class_id: int
    student_id: int

class Update(BaseModel):
    class_id: int | None = None
    student_id: int | None = None

class Out(BaseModel):
    id: int
    class_id: int
    student_id: int
    created: datetime
    updated: datetime

    class Config:
        from_attributes = True