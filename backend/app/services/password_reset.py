import sys
from pathlib import Path

import hashlib
import secrets
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).resolve().parents[1]))

from db.models import Student, OneTimeToken
from db.database import SessionLocal


def create_reset_token(db, student_id: int) -> str:

    raw_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    reset_token = OneTimeToken(
        student_id=student_id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )

    db.add(reset_token)
    db.commit()

    return raw_token

def validate_reset_token(db, token: str) -> OneTimeToken | None:

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    return db.query(OneTimeToken).filter(
            OneTimeToken.token_hash == token_hash,
            OneTimeToken.used_at.is_(None),
            OneTimeToken.expires_at > datetime.utcnow()
        ).first()