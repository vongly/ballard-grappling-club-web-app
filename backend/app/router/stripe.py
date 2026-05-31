import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db.database import get_db, SessionLocal
from db.models import Student, Product

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.security import get_current_student, get_current_superuser
from services.stripe_services import StripeServices

sys.path.append(str(Path(__file__).resolve().parents[2]))

from env import STRIPE_KEY, FRONTEND_URL_PUBLIC


router = APIRouter()

class CheckoutPayload(BaseModel):
    product_id: int


@router.post("/checkout")
def checkout(
    payload: CheckoutPayload,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    product = db.query(Product).filter(Product.id == payload.product_id).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    stripe_service = StripeServices(api_key=STRIPE_KEY,db=db)

    session = stripe_service.create_checkout(
        student_id=student.id,
        product_id=product.id,
        frontend_url=f'{FRONTEND_URL_PUBLIC}/stripe/checkout',
    )

    return {
        "success": True,
        "checkout_url": session.url,
        "session_id": session.id,
    }



