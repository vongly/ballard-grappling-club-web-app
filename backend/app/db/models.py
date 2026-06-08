from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign
from sqlalchemy import (
    DateTime,
    String,
    ForeignKey,
    DateTime,
    Boolean,
    func,
    Integer,
    JSON,
    UniqueConstraint,
    and_,
    false
)
from .database import Base

from datetime import datetime, date, time

class Student(Base):
    __tablename__ = 'students'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first: Mapped[str] = mapped_column(nullable=False)
    last: Mapped[str] = mapped_column(nullable=False)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    phone: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True)
    birthdate: Mapped[date] = mapped_column(nullable=False)

    address_1: Mapped[str] = mapped_column(nullable=False)
    address_2: Mapped[str] = mapped_column(nullable=True)
    city: Mapped[str] = mapped_column(nullable=False)
    state: Mapped[str] = mapped_column(nullable=False)
    zipcode: Mapped[str] = mapped_column(nullable=False)

    photo_url: Mapped[str] = mapped_column(nullable=True)
    waiver_url: Mapped[str] = mapped_column(nullable=True)

    emergency_contact_name: Mapped[str] = mapped_column(nullable=False)
    emergency_contact_relationship: Mapped[str] = mapped_column(nullable=False)
    emergency_contact_phone: Mapped[str] = mapped_column(nullable=False)

    type: Mapped[str] = mapped_column(default=1, nullable=False)
    # 0 - Adult Student -> Staff (Free Tuition)
    # 1 - Adult Student -> Paid User
    # 2 - Adult Student -> Free Tuition
    trial_initiated: Mapped[date] = mapped_column(default=None, nullable=True)
    email_verified: Mapped[int] = mapped_column(default=1, nullable=False, server_default=false())


    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    subscriptions = relationship("Subscription", back_populates="student")
    password_reset_tokens: Mapped[list["OneTimeToken"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan"
    )
    
class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[str] = mapped_column(unique=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    currency: Mapped[str] = mapped_column(nullable=False)
    price_id: Mapped[str] = mapped_column(nullable=False)
    recurring: Mapped[int] = mapped_column(nullable=False)
    unit_amount: Mapped[int] = mapped_column(nullable=False)
    active: Mapped[int] = mapped_column(nullable=False)
    product_order: Mapped[int] = mapped_column(default=0)
    upgrade: Mapped[int] = mapped_column(default=0, nullable=True)
    subscription_classes_per_week: Mapped[int] = mapped_column(nullable=True)
    # Null -> no subscription
    # 0 -> unlimited
    # 1-7 -> classes per week
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    stripe_customer_id: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    stripe_subscription_id: Mapped[str] = mapped_column(unique=True, nullable=True, index=True)
    stripe_price_id: Mapped[str] = mapped_column(nullable=True)
    status: Mapped[int] = mapped_column(default=0, nullable=False)
    # 0 -> no activity
    # 1 -> active
    # 2 -> canceled
    # 3 -> past_due
    # 4 -> unpaid
    classes_available: Mapped[int] = mapped_column(default=0, nullable=True)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    student = relationship("Student",back_populates="subscriptions")
    product = relationship(
        "Product",
        primaryjoin=foreign(stripe_price_id) == Product.price_id,
        viewonly=True,
        uselist=False,
    )

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)

    student_id: Mapped[str] = mapped_column(nullable=False)
    product_id: Mapped[str] = mapped_column(nullable=False)

    stripe_session_id: Mapped[str] = mapped_column(unique=True, index=True)
    stripe_customer_id: Mapped[str] = mapped_column(index=True, nullable=False)
    stripe_subscription_id: Mapped[str] = mapped_column(index=True, nullable=False)

    payment_status: Mapped[str | None] = mapped_column(nullable=True)
    status: Mapped[str | None] = mapped_column(nullable=True)
    mode: Mapped[str | None] = mapped_column(nullable=True)

    currency: Mapped[str | None] = mapped_column(nullable=True)
    amount_total: Mapped[int | None] = mapped_column(nullable=True)
    amount_subtotal: Mapped[int | None] = mapped_column(nullable=True)

    raw_session: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class Class(Base):
    __tablename__ = 'classes'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    class_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration: Mapped[int] = mapped_column(nullable=False)
    type: Mapped[int] = mapped_column(default=0, nullable=False)
    # 0 - Adult BJJ
    promotion: Mapped[int] = mapped_column(default=0, nullable=False)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class ClassAttendance(Base):
    __tablename__ = "class_attendance"

    __table_args__ = (
        UniqueConstraint(
            "class_id",
            "student_id",
            name="uq_class_attendance_class_student",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    class_id: Mapped[int] = mapped_column(nullable=False)
    student_id: Mapped[int] = mapped_column(nullable=False)

    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class StripeEvent(Base):
    __tablename__ = "stripe_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(unique=True, index=True)
    status: Mapped[int] = mapped_column(default=0, nullable=True)
    # -1 -> failed
    # 0 -> processing
    # 1 -> completed
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class OneTimeToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    purpose: Mapped[str] = mapped_column(String(32), index=True, nullable=True)
    # e.g. "password_reset", "email_confirmation", "invite"
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    student: Mapped["Student"] = relationship(back_populates="password_reset_tokens")