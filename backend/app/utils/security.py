import sys
from pathlib import Path

from datetime import datetime, timedelta, timezone

import hashlib
from passlib.context import CryptContext

from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from db.database import SessionLocal
from db.models import Student

sys.path.append(str(Path(__file__).resolve().parents[2]))

from env import SECRET_KEY, ALGORITHM


ACCESS_TOKEN_EXPIRE_MINUTES = 2880

pwd_context = CryptContext(schemes=['argon2'], deprecated='auto')


def hash_password(password: str) -> str:
    # pre-hash to remove length limitation
    sha = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.hash(sha)

def verify_password(password: str, hashed: str) -> bool:
    sha = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.verify(sha, hashed)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def check_for_student(token: str = Depends(oauth2_scheme)):
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        student_id = payload.get("sub")

        if not student_id:
            return None

        student_id = int(student_id)

    except JWTError:
        return None

    db = SessionLocal()
    try:
        return db.query(Student).filter(Student.id == student_id).first()
    finally:
        db.close()


def get_current_student(student: Student | None = Depends(check_for_student)):
    if student is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return student

def get_current_superuser(student: Student | None = Depends(check_for_student)):
    if student is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    if student.type != 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superuser access required")

    return student