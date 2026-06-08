import sys
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from db.database import SessionLocal, get_db
from db.models import Student
from db.schemas.PasswordResetToken import ForgotPasswordRequest, ResetPasswordRequest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.password_reset import create_reset_token, validate_reset_token
from services.email_services import render_email, send_email
from utils.security import verify_password, create_access_token, hash_password

sys.path.append(str(Path(__file__).resolve().parents[2]))

from env import FRONTEND_URL_PUBLIC


def send_password_reset_email(to_email: str, reset_link: str):
    html = render_email(
        "password_reset.html",
        reset_link=reset_link,
    )

    send_email(
        to_email=to_email,
        subject="Reset your password",
        body_html=html,
    )



router = APIRouter()

@router.post('')
def login(payload: dict):
    email = payload.get('email')
    password = payload.get('password')

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

@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    student = (
        db.query(Student)
        .filter(Student.email == request.email)
        .first()
    )

    # Always return success (prevents email enumeration)
    if not student:
        return {
            "message": "If the email exists, a reset link has been sent."
        }

    # Create reset token (stores hashed version in DB)
    token = create_reset_token(db, student.id)

    # Build frontend reset link
    reset_link = f"{FRONTEND_URL_PUBLIC}/reset-password?token={token}"

    # Send email (NOT async)
    send_password_reset_email(
        to_email=student.email,
        reset_link=reset_link,
    )

    return {
        "message": "If the email exists, a reset link has been sent."
    }


@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    reset_record = validate_reset_token(db, request.token)

    if not reset_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired token",
        )

    student = (
        db.query(Student)
        .filter(Student.id == reset_record.student_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=400,
            detail="User not found",
        )

    try:
        # Update password
        student.password_hash = hash_password(request.new_password)

        # Mark token as used
        reset_record.used_at = datetime.utcnow()

        db.add(student)
        db.add(reset_record)

        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not reset password",
        )

    return {
        "message": "Password updated successfully"
    }