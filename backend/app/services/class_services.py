import sys
from pathlib import Path
from datetime import datetime, date, timedelta, timezone
from dateutil.relativedelta import relativedelta

from sqlalchemy.orm import Session

sys.path.append(str(Path(__file__).resolve().parents[1]))

from db.models import Student, Product, Subscription, Class, ClassAttendance
from db.database import SessionLocal

sys.path.append(str(Path(__file__).resolve().parents[2]))

from env import STRIPE_KEY, TRIAL_LENGTH



from sqlalchemy.orm import Session
from typing import Tuple, List, Optional


today = datetime.today()

class ClassAttendanceService:
    def __init__(self, db: Session, class_id: int):
        self.db = db
        self.class_obj = self.db.query(Class).filter(Class.id == class_id).first()

    def check_eligibility(self, student_id: int):
        student = self.db.query(Student).filter(Student.id == student_id).first()

        if not student:
            return {"status": False, "reason": "student not found"}

        subscription = self.db.query(Subscription).filter(Subscription.student_id == student_id).first()

        if self.class_obj.promotion == 1:
            return {"status": True, "reason": "promotional class"}

        elif subscription:
            if subscription.status == 1:
                return {"status": True, "reason": "active subscription"}
            elif subscription.classes_available > 0:
                return {"status": True, "reason": "classes available"}

        else: # -> no subscription
            # 1 -> check staff
            if student.type == "0":
                return {"status": True, "reason": "staff member"            }
            # 2 -> check if trial needs to be initiated
            elif student.trial_initiated is None:
                return {"status": True, "reason": "trial no yet initiated"}
            # 3 -> check if trial is in progress
            elif today < student.trial_initiated + timedelta(days=7):
                return {"status": True, "reason": "trial in progress"}
        
        return {"status": False, "reason": "ineligible"}
        
    def check_student_in(self, student_id):
        is_eligible = self.check_eligibility(student_id=student_id)

        if not is_eligible["status"]:
            return False # -> needs to purchase class or sub
        else:
            return True # -> take actions depend on reason