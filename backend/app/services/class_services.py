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

        # Special Users Flow
        if self.student.type == "0":
            return {"status": True, "reason": "staff member"}
        elif self.student.type == "100": # Hoa membership
            return {"status": True, "reason": "hoa"}

        # Subscription flow
        if self.subscription:
            if self.subscription.status == 1:
                return {"status": True, "reason": "active subscription"}

            if self.subscription.classes_available > 0:
                return {"status": True, "reason": "classes available"}

        # No subscription flow
        if self.student.trial_initiated is None:
            return {"status": True, "reason": "trial initiated"}

        if self.student.trial_initiated + timedelta(days=7) > self.today:
            return {"status": True, "reason": "trial in progress"}

        return {"status": False, "reason": "ineligible"}

    def check_student_in(self):
        send_first_class_follow_up = False

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
                send_first_class_follow_up = True

        elif reason in ["active subscription", "staff member", "trial initiated, hoa"]:
            if not self.student.trial_initiated:
                self.student.trial_initiated = self.today
                send_first_class_follow_up = True

        self.db.commit()

        if send_first_class_follow_up:
            import traceback

            try:
                welcome_body = render_email(
                    template_name="first_class_follow_up.html",
                    name=self.student.first,
                    title="Thanks for Joining Us!",
                )

                send_email(
                    to_email=self.student.email,
                    subject="Thanks for Joining Us!!",
                    body_html=welcome_body,
                )

            except Exception as e:
                print(f"Failed to send first class follow-up {self.student.id}: {e}")
                traceback.print_exc()

        return {"status": "success", "reason": reason, "action": "route to success"}