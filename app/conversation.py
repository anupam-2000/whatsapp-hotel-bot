from datetime import datetime, date
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Booking

def handle_message(phone: str, message: str) -> str:
    message = message.strip()
    db: Session = SessionLocal()

    try:
        booking = (
            db.query(Booking)
            .filter(Booking.phone == phone)
            .order_by(Booking.id.desc())
            .first()
        )

        # Start new booking if none or completed
        if not booking or booking.step == 5 or message.lower() == "restart":
            booking = Booking(
                phone=phone,
                step=1,
                created_date=date.today()
            )
            db.add(booking)
            db.commit()
            return "May I have your name?"

        if booking.step == 1:
            booking.name = message.title()
            booking.step = 2
            db.commit()
            return "Which city/location are you booking for?"

        if booking.step == 2:
            booking.location = message.title()
            booking.step = 3
            db.commit()
            return "What is your check-in date? (YYYY-MM-DD)"

        if booking.step == 3:
            try:
                checkin_date = datetime.strptime(message, "%Y-%m-%d").date()
                if checkin_date < date.today():
                    return "❌ Check-in date cannot be in the past."
                booking.checkin = message
                booking.step = 4
                db.commit()
                return "What is your check-out date? (YYYY-MM-DD)"
            except ValueError:
                return "❌ Please enter date in YYYY-MM-DD format."

        if booking.step == 4:
            try:
                checkout_date = datetime.strptime(message, "%Y-%m-%d").date()
                if checkout_date <= datetime.strptime(booking.checkin, "%Y-%m-%d").date():
                    return "❌ Check-out must be after check-in."
                booking.checkout = message
                booking.step = 5
                db.commit()
                return "✅ Booking saved! Type *restart* to make another booking."
            except ValueError:
                return "❌ Please enter date in YYYY-MM-DD format."

        return "Type *restart* to start a new booking."

    finally:
        db.close()
