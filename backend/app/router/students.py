import sys
from pathlib import Path
from datetime import date, datetime

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import boto3
from botocore.client import Config
from io import BytesIO
from PIL import Image


sys.path.append(str(Path(__file__).resolve().parents[1]))

from db.database import SessionLocal, get_db
from db.models import Student

from utils.security import (
    hash_password,
    get_current_student,
    verify_password,
    create_access_token
)
from utils import helpers
from services.email_services import send_email, render_email

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
    FRONTEND_URL_PUBLIC,
    MY_EMAIL,
)



router = APIRouter()

@router.post('')
async def create_student(
    first: str=Form(...),
    last: str=Form(...),
    password: str=Form(...),
    phone: str=Form(...),
    email: str=Form(...),
    birthdate: date=Form(...),
    address_1: str=Form(...),
    address_2: str | None = Form(None),
    city: str=Form(...),
    state: str=Form(...),
    zipcode: str=Form(...),
    emergency_contact_name: str=Form(...),
    emergency_contact_relationship: str=Form(...),
    emergency_contact_phone: str=Form(...),
    profile_picture: UploadFile=File(...),
    waiver: UploadFile=File(...),
    db: Session=Depends(get_db)
    ):

    now = datetime.now()
    now_str = now.strftime('%Y.%m.%d.%H.%M.%S')

    student = Student(
        first=first,
        last=last,
        password_hash=hash_password(password),
        phone=phone,
        email=email,
        birthdate=birthdate,
        address_1=address_1,
        address_2=address_2,
        city=city,
        state=state,
        zipcode=zipcode,
        emergency_contact_name=emergency_contact_name,
        emergency_contact_relationship=emergency_contact_relationship,
        emergency_contact_phone=emergency_contact_phone,
    )

    try:
        db.add(student)
        db.flush()

        S3_CLIENT = boto3.client(
            's3',
            endpoint_url=S3_URL,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
        )

        s3_check = helpers.CheckS3Bucket(S3_CLIENT, BUCKET_NAME)
        s3_check.ensure_bucket()
        s3_check.ensure_key(PROFILE_PICTURE_PREFIX)
        s3_check.ensure_key(WAIVER_PREFIX)

        # ================= PROFILE PICTURE =================

        image_pp = Image.open(profile_picture.file)
        image_pp = image_pp.convert('RGB')

        buffer_pp = BytesIO()

        image_pp.save(
            buffer_pp,
            format='JPEG',
            quality=90,
        )

        buffer_pp.seek(0)

        filename_pp = f'{student.id}.jpg'

        object_key_pp = (
            f'{PROFILE_PICTURE_PREFIX}/'
            f'{filename_pp}'
        )

        S3_CLIENT.upload_fileobj(
            buffer_pp,
            BUCKET_NAME,
            object_key_pp,
            ExtraArgs={'ContentType': 'image/jpeg'},
        )

        # ================= WAIVER =================

        waiver_bytes = await waiver.read()

        waiver_buffer = BytesIO(waiver_bytes)

        filename_waiver = f'{student.id}_{now_str}.pdf'

        object_key_waiver = (
            f'{WAIVER_PREFIX}/'
            f'{filename_waiver}'
        )

        S3_CLIENT.upload_fileobj(
            waiver_buffer,
            BUCKET_NAME,
            object_key_waiver,
            ExtraArgs={'ContentType': 'application/pdf'},
        )

        # ================= URLS =================

        student.photo_url = (
            f'{PROFILE_PICTURE_PREFIX}/'
            f'{filename_pp}'
        )

        student.waiver_url = (
            f'{WAIVER_PREFIX}/'
            f'{filename_waiver}'
        )

        db.commit()
        db.refresh(student)

        import traceback

        try:
            welcome_body = render_email(
                template_name="welcome.html",
                name=student.first,
                title="Welcome!",
                frontend_url=FRONTEND_URL_PUBLIC,
            )

            send_email(
                to_email=student.email,
                subject="Welcome!",
                body_html=welcome_body,
            )

            welcome_body_internal = render_email(
                template_name="welcome_internal.html",
                id=student.id,
                first=student.first,
                last=student.last,
                phone=student.phone,
                email=student.email,
                birthdate=student.birthdate,
                join_date=student.created,
                title="Welcome!",
                frontend_url=FRONTEND_URL_PUBLIC,
            )

            send_email(
                to_email=MY_EMAIL,
                subject="New Student Account",
                body_html=welcome_body_internal,
            )

        except Exception as e:
            print(f"Failed to send welcome emails for student {student.id}: {e}")
            traceback.print_exc()


    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail='User with this email already exists'
        )

    db = SessionLocal()

    student = db.query(Student).filter(Student.email == email).first()

    db.close()

    if not student:
        raise HTTPException(status_code=401, detail="Bad credentials")

    if not verify_password(password, student.password_hash):
        raise HTTPException(status_code=401, detail="Bad credentials")

    token = create_access_token(
        data={"sub": str(student.id)}
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.get("/me")
async def get_me(student=Depends(get_current_student)):

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

    presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": student.photo_url.lstrip("/"),
        },
        ExpiresIn=3600,
    )

    student.presigned_url = presigned_url.replace(S3_URL, S3_URL_CDN)

    return student
