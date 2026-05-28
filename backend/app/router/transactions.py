import sys
from pathlib import Path
from datetime import date, datetime

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List


sys.path.append(str(Path(__file__).resolve().parents[1]))

from db.database import SessionLocal, get_db
from db.models import Transaction
from db.schemas.Transaction import Create, Update, Out

sys.path.append(str(Path(__file__).resolve().parents[2]))


router = APIRouter()


@router.post("/", response_model=Out)
def create_transaction(payload: Create, db: Session = Depends(get_db)):

    existing = db.query(Transaction).filter(
        Transaction.stripe_checkout_session_id == payload.stripe_checkout_session_id
    ).first()

    if existing:
        return existing

    raw_session = payload.raw_session or {}

    transaction = Transaction(
        student_id=payload.student_id,
        product_id=payload.product_id,

        stripe_checkout_session_id=payload.stripe_checkout_session_id,
        stripe_payment_intent_id=payload.stripe_payment_intent_id,
        stripe_invoice_id=payload.stripe_invoice_id,

        amount_total=payload.amount_total,
        currency=payload.currency,
        price_id=payload.price_id,
        type=payload.type,
        status=payload.status,

        raw_session=raw_session,
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


@router.get("/", response_model=List[Out])
def get_transactions(
    student_id: Optional[int] = None,
    product_id: Optional[int] = None,
    stripe_checkout_session_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):

    query = db.query(Transaction)

    if student_id is not None:
        query = query.filter(Transaction.student_id == student_id)

    if product_id is not None:
        query = query.filter(Transaction.product_id == product_id)

    if stripe_checkout_session_id:
        query = query.filter(
            Transaction.stripe_checkout_session_id == stripe_checkout_session_id
        )

    if status:
        query = query.filter(Transaction.status == status)

    return query.order_by(Transaction.created.desc()).all()


@router.get("/{transaction_id}", response_model=Out)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):

    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return transaction