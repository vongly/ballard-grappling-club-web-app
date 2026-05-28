import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from db.database import SessionLocal
from db.models import Student

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.security import verify_password, create_access_token

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