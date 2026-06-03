import sys
from pathlib import Path
from datetime import datetime, date, timedelta, timezone
from dateutil.relativedelta import relativedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import List

import boto3
from botocore.client import Config
from io import BytesIO
from PIL import Image

sys.path.append(str(Path(__file__).resolve().parents[1]))

from db.database import get_db
from db.models import Class, ClassAttendance, Student
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


sys.path.append(str(Path(__file__).resolve().parents[1]))

from env import (
    BUCKET_NAME,
    PROFILE_PICTURE_PREFIX,
    WAIVER_PREFIX,
    S3_URL,
    S3_URL_CDN,
    S3_ACCESS_KEY,
    S3_SECRET_KEY,
    S3_REGION,
    MY_EMAIL,
)


from pydantic import BaseModel
from datetime import datetime


class StudentOut(BaseModel):
    id: int
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class ClassOut(BaseModel):
    id: int
    name: str
    start_time: datetime

    class Config:
        from_attributes = True


class AttendanceOut(BaseModel):
    id: int
    class_id: int
    student_id: int
    created: datetime
    updated: datetime

    student: StudentOut
    class_obj: ClassOut

    class Config:
        from_attributes = True

router = APIRouter()

@router.get(
    "/{class_id:int}/students",
    #response_model=list[StudentOut]
)
def get_students_for_class(
    class_id: int,
    db: Session = Depends(get_db),
):
    students_obj = (
        db.query(Student)
        .join(
            ClassAttendance,
            Student.id == ClassAttendance.student_id
        )
        .filter(
            ClassAttendance.class_id == class_id
        )
        .all()
    )

    client_kwargs = {
        "service_name": "s3",
        "endpoint_url": S3_URL,
        "aws_access_key_id": S3_ACCESS_KEY,
        "aws_secret_access_key": S3_SECRET_KEY,
    }

    if S3_REGION:
        client_kwargs["region_name"] = S3_REGION
        client_kwargs["config"] = Config(signature_version="s3v4")

    s3_client = boto3.client(**client_kwargs)


    students = []
    for student in students_obj:

        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": student.photo_url.lstrip("/"),
            },
            ExpiresIn=3600,
        )
        students.append(
            {
                "phone": student.phone,
                "photo_url": student.photo_url,
                "updated": student.updated,
                "email": student.email,
                "emergency_contact_name": student.emergency_contact_name,
                "birthdate": student.birthdate,
                "waiver_url": student.waiver_url,
                "first": student.first,
                "address_1": student.address_1,
                "emergency_contact_relationship": student.emergency_contact_relationship,
                "address_2": student.address_2,
                "emergency_contact_phone": student.emergency_contact_phone,
                "id": student.id,
                "city": student.city,
                "type": student.type,
                "last": student.last,
                "state": student.state,
                "trial_initiated": student.trial_initiated,
                "zipcode": student.zipcode,
                "created": student.created,
                "presigned_url": presigned_url.replace(S3_URL, S3_URL_CDN)
            }
        )

    return students