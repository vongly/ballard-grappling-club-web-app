import sys
from pathlib import Path
from datetime import date, datetime

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session


sys.path.append(str(Path(__file__).resolve().parents[1]))

from db.database import SessionLocal, get_db
from db.models import Product

sys.path.append(str(Path(__file__).resolve().parents[2]))


router = APIRouter()

@router.get("")
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()

    return products