from datetime import datetime
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Booking

def handle_message(phone: str, message: str) -> str:
    message = message.strip().lower()
    db: Session = SessionLocal()

    try:
        # Restart anytime
        if message == "restart":
            db.query(Booking).filter(Booking.phone == phone).delete()
            db.commit()
            return "🔄 Restarted! May I have your name?"

        booking = (
            db.query(Booking)
            .filter(Booking.phone == phone)
            .order_by(Booking.id.desc())
            .first()
        )

        # New user or new test booking
        if not booking:
            booking = Booking(
                phone=phone,
                step=1
            )
            db.add(booking)
            db.commit()
            return "May I have your name?"

        if booking.step == 1:
            booking.name = message.title()
            booking.step = 2
            db.commit()
            return f"Nice to meet you, {booking.name}! What is your check-in date? (YYYY-MM-DD)"

        if booking.step == 2:
            try:
                datetime.strptime(message, "%Y-%m-%d")
                booking.checkin = message
                booking.step = 3
                db.commit()
                return "Got it! What is your check-out date? (YYYY-MM-DD)"
            except ValueError:
                return "❌ Please enter the check-in date in YYYY-MM-DD format."

        if booking.step == 3:
            try:
                datetime.strptime(message, "%Y-%m-%d")
                booking.checkout = message
                booking.step = 4
                db.commit()
                return "✅ Booking saved! Type *restart* to make another booking."
            except ValueError:
                return "❌ Please enter the check-out date in YYYY-MM-DD format."

        return "Type *restart* to create a new booking."

    finally:
        db.close()
