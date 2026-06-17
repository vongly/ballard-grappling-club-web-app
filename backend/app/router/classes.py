import sys
from pathlib import Path
from datetime import datetime, date, timedelta, timezone
from dateutil.relativedelta import relativedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

sys.path.append(str(Path(__file__).resolve().parents[1]))

from db.database import get_db
from db.models import Class, ClassAttendance
from db.schemas.Class import (
    Create as ClassCreate,
    Update as ClassUpdate,
    Out as ClassOut
)
from db.schemas.ClassAttendance import (
    Create as ClassAttendanceCreate,
    Update as ClassAttendanceUpdate,
    Out as ClassAttendanceOut
)

from services.class_services import ClassAttendanceService
from utils.security import check_for_student

from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")
UTC = ZoneInfo("UTC")

router = APIRouter()

@router.get("/", response_model=List[ClassOut])
def get_all_classes(db: Session = Depends(get_db)):
    return db.query(Class).order_by(Class.class_datetime).all()

@router.get("/{class_id}", response_model=ClassOut)
def get_class(class_id: int, db: Session = Depends(get_db)):
    record = db.query(Class).filter(Class.id == class_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Class not found")

    return record

@router.post("/", response_model=ClassOut)
def create_class(payload: ClassCreate, db: Session = Depends(get_db)):

    # payload.class_datetime is assumed to be "Pacific wall time"
    naive = payload.class_datetime.replace(tzinfo=PACIFIC)

    utc_dt = naive.astimezone(UTC)

    new_class = Class(
        name=payload.name,
        class_datetime=utc_dt,
        duration=payload.duration,
        type=payload.type,
        promotion=payload.promotion,
    )

    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    return new_class

@router.post("/batch", response_model=List[ClassOut])
def create_batch(payload: List[ClassCreate], db: Session = Depends(get_db)):
    objects = []

    for item in payload:
        naive = item.class_datetime.replace(tzinfo=PACIFIC)
        utc_dt = naive.astimezone(UTC)

        objects.append(
            Class(
                name=item.name,
                class_datetime=utc_dt,
                duration=item.duration,
                type=item.type,
                promotion=item.promotion,
            )
        )

    db.add_all(objects)
    db.commit()

# CLASS CHECKIN

@router.get("/{class_id}/checkin")
def class_checkin(
    class_id: int,
    db: Session = Depends(get_db),
    student=Depends(check_for_student),
):

    if not student:
        return {
            "authenticated": False,
            "status": "failed",
            "action": "redirect_to_signin",
            "redirect_url": f"/signin?next=/{class_id}/checkin",
            "class_data": None,
        }
    service = ClassAttendanceService(db=db, class_id=class_id, student_id=student.id)

    result = service.check_student_in()

    return {
        "authenticated": True,
        "status": result["status"],
        "action": result["action"],
        "reason": result.get("reason"),
        "class_data": {
            "class_id": class_id,
        },
    }