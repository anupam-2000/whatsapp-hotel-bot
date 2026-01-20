from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Booking

def handle_message(phone: str, message: str) -> str:
    message = message.strip()
    db: Session = SessionLocal()

    try:
        # Restart flow
        if message.lower() == "restart":
            booking = Booking(phone=phone, step=1)
            db.add(booking)
            db.commit()
            return "🔄 Restarted! May I have your name?"

        booking = (
            db.query(Booking)
            .filter(Booking.phone == phone)
            .order_by(Booking.id.desc())
            .first()
        )

        if not booking:
            booking = Booking(phone=phone, step=1)
            db.add(booking)
            db.commit()
            return "May I have your name?"

        # STEP 1: Name
        if booking.step == 1:
            booking.name = message.title()
            booking.step = 2
            db.commit()
            return f"Nice to meet you, {booking.name}! Which city is your hotel in?"

        # STEP 2: Location
        if booking.step == 2:
            booking.location = message.title()
            booking.step = 3
            db.commit()
            return (
                "When do you want to check in?\n"
                "1️⃣ Today\n"
                "2️⃣ Tomorrow\n"
                "3️⃣ Day after tomorrow\n"
                "4️⃣ Other"
            )

        # STEP 3: Check-in choice
        if booking.step == 3:
            today = datetime.today().date()

            if message == "1":
                booking.checkin = today.isoformat()
            elif message == "2":
                booking.checkin = (today + timedelta(days=1)).isoformat()
            elif message == "3":
                booking.checkin = (today + timedelta(days=2)).isoformat()
            elif message == "4":
                booking.step = 31
                db.commit()
                return "Please enter your check-in date (YYYY-MM-DD)"
            else:
                return "❌ Please reply with 1, 2, 3, or 4."

            booking.step = 4
            db.commit()
            return "Got it! What is your check-out date? (YYYY-MM-DD)"

        # STEP 31: Manual check-in date
        if booking.step == 31:
            try:
                checkin_date = datetime.strptime(message, "%Y-%m-%d").date()
                if checkin_date < datetime.today().date():
                    return "❌ Check-in date cannot be in the past."

                booking.checkin = checkin_date.isoformat()
                booking.step = 4
                db.commit()
                return "Got it! What is your check-out date? (YYYY-MM-DD)"
            except ValueError:
                return "❌ Please enter date in YYYY-MM-DD format."

        # STEP 4: Check-out
        if booking.step == 4:
            try:
                checkout_date = datetime.strptime(message, "%Y-%m-%d").date()
                if checkout_date <= datetime.fromisoformat(booking.checkin).date():
                    return "❌ Check-out must be after check-in."

                booking.checkout = checkout_date.isoformat()
                booking.step = 5
                db.commit()
                return "✅ Booking saved! Type *restart* to make another booking."
            except ValueError:
                return "❌ Please enter date in YYYY-MM-DD format."

        return "Type *restart* to create a new booking."

    finally:
        db.close()
