import sys
from pathlib import Path
from datetime import datetime, date, timedelta, timezone
from dateutil.relativedelta import relativedelta

from sqlalchemy.orm import Session

sys.path.append(str(Path(__file__).resolve().parents[1]))

from db.models import Student, Product, Subscription, Class, ClassAttendance
from db.database import SessionLocal

from services.email_services import send_email, render_email

sys.path.append(str(Path(__file__).resolve().parents[2]))

from env import MY_EMAIL



from sqlalchemy.orm import Session
from typing import Tuple, List, Optional


today = datetime.today()

class ClassAttendanceService:
    def __init__(self, db: Session, class_id: int, student_id: int):
        self.db = db

        self.class_obj = self.db.query(Class).filter(Class.id == class_id).first()
        self.student = self.db.query(Student).filter(Student.id == student_id).first()
        self.subscription = self.db.query(Subscription).filter(Subscription.student_id == student_id).first()

        self.today = date.today()

    def check_eligibility(self):
        if not self.student:
            return {"status": False, "reason": "student not found"}

        if not self.class_obj:
            return {"status": False, "reason": "class not found"}

        # Promotional class overrides everything
        if self.class_obj.promotion == 1:
            return {"status": True, "reason": "promotional class"}

        # Subscription flow
        if self.subscription:
            if self.subscription.status == 1:
                return {"status": True, "reason": "active subscription"}

            if self.subscription.classes_available > 0:
                return {"status": True, "reason": "classes available"}

        # No subscription flow
        if self.student.type == "0":
            return {"status": True, "reason": "staff member"}

        if self.student.trial_initiated is None:
            return {"status": True, "reason": "trial initiated"}

        if self.student.trial_initiated + timedelta(days=7) > self.today:
            return {"status": True, "reason": "trial in progress"}

        return {"status": False, "reason": "ineligible"}

    def check_student_in(self):
        result = self.check_eligibility()

        status = result["status"]
        reason = result["reason"]

        if not status:
            if reason == "student not found":
                return {"status": "failed", "action": "route to register"}

            return {"status": "failed", "reason": reason, "action": "route to purchase"}

        existing = self.db.query(ClassAttendance).filter_by(class_id=self.class_obj.id,student_id=self.student.id).first()
        if existing:
            return {
                "status": "success",
                "reason": "already checked in",
                "action": "route to success",
            }

        attendance = ClassAttendance(class_id=self.class_obj.id, student_id=self.student.id)
        self.db.add(attendance)

        if reason == "classes available":
            if self.subscription:
                self.subscription.classes_available -= 1

        elif reason in ["active subscription", "staff member", "trial initiated"]:
            if not self.student.trial_initiated:
                self.student.trial_initiated = self.today

                import traceback

                try:
                    welcome_body = render_email(
                        template_name="welcome.html",
                        name=self.student.first,
                        title="Welcome!",
                    )

                    send_email(
                        to_email=self.student.email,
                        subject="Welcome!",
                        body_html=welcome_body,
                    )

                    welcome_body_internal = render_email(
                        template_name="welcome_internal.html",
                        id=self.student.id,
                        first=self.student.first,
                        last=self.student.last,
                        phone=self.student.phone,
                        email=self.student.email,
                        birthdate=self.student.birthdate,
                        join_date=self.student.created,
                        title="Welcome!",
                    )

                    send_email(
                        to_email=MY_EMAIL,
                        subject="New Student Account",
                        body_html=welcome_body_internal,
                    )

                except Exception as e:
                    print(f"Failed to send welcome emails for student {self.student.id}: {e}")
                    traceback.print_exc()

        self.db.commit()

        return {"status": "success", "reason": reason, "action": "route to success"}