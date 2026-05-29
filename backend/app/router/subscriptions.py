import sys
from pathlib import Path
from datetime import date, datetime

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List


sys.path.append(str(Path(__file__).resolve().parents[1]))

from db.database import SessionLocal, get_db
from db.models import Subscription, Student, Product
from db.schemas.Subscription import Create, Update, Out

from utils.security import get_current_superuser, get_current_student

sys.path.append(str(Path(__file__).resolve().parents[2]))


router = APIRouter()


@router.get("/", response_model=List[Out] | None)
async def get_all_subscriptions(
    db: Session = Depends(get_db),
    _: Student = Depends(get_current_superuser),

    skip: int = 0,
    limit: int = 50,

    student_id: int | None = Query(None),
    status: int | None = Query(None),
    stripe_customer_id: str | None = Query(None),
    stripe_price_id: str | None = Query(None),
):
    query = db.query(Subscription)

    if student_id is not None:
        query = query.filter(Subscription.student_id == student_id)

    if status is not None:
        query = query.filter(Subscription.status == status)

    if stripe_customer_id is not None:
        query = query.filter(Subscription.stripe_customer_id == stripe_customer_id)

    if stripe_price_id is not None:
        query = query.filter(Subscription.stripe_price_id == stripe_price_id)

    return query.offset(skip).limit(limit).all()

@router.get("/{sub_id:int}", response_model=Out | None)
async def get_subscription_by_id(
    sub_id: int,
    db: Session = Depends(get_db),
    _: Student = Depends(get_current_superuser),
):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()


    return sub

@router.get("/me", response_model=Out | None)
async def get_my_subscription(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    subscription = db.query(Subscription).filter(Subscription.student_id == student.id).first()

    return subscription