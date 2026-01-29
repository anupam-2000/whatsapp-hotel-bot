from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Booking
import pandas as pd
import os

# ==========================
# LOAD CSV DATA
# ==========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

employees_df = pd.read_csv(os.path.join(DATA_DIR, "employees.csv"), encoding="utf-8-sig")
hotels_df = pd.read_csv(os.path.join(DATA_DIR, "hotels.csv"), encoding="utf-8-sig")
booking_history_df = pd.read_csv(os.path.join(DATA_DIR, "booking_history.csv"), encoding="utf-8-sig")

employees_df.columns = employees_df.columns.str.strip().str.lower()
hotels_df.columns = hotels_df.columns.str.strip().str.lower()
booking_history_df.columns = booking_history_df.columns.str.strip().str.lower()

PRICE_COL = next(
    c for c in hotels_df.columns
    if c in {"price_per_night", "price", "room_price", "rate"}
)

# ==========================
# HELPERS
# ==========================

def get_employee(name: str):
    df = employees_df[
        employees_df["employee_name"].str.lower() == name.lower()
    ]
    return None if df.empty else df.iloc[0]


def get_previous_good_hotel(employee_id, city, min_rating=4):
    history = booking_history_df[
        (booking_history_df["employee_id"] == employee_id) &
        (booking_history_df["city"].str.lower() == city.lower()) &
        (booking_history_df["rating"] >= min_rating)
    ]

    if history.empty:
        return None

    merged = history.merge(hotels_df, on="hotel_id", how="left")
    return merged.iloc[0]


def recommend_hotels(city, price_cap=None):
    df = hotels_df[hotels_df["city"].str.lower() == city.lower()]

    if price_cap is not None:
        df = df[df[PRICE_COL] <= price_cap]

    return df.sort_values(
        ["star_rating", PRICE_COL],
        ascending=[False, True]
    ).head(3)


def build_recommendation_text(city, price_cap=None):
    recs = recommend_hotels(city, price_cap)

    if recs.empty:
        return "❌ No hotels available for this location."

    msg = "Here are some recommended hotels:\n"
    for i, row in enumerate(recs.itertuples(), 1):
        msg += (
            f"{i}️⃣ {row.hotel_name} – "
            f"₹{getattr(row, PRICE_COL)}/night ⭐{row.star_rating}\n"
        )

    msg += "\nReply with the hotel number."
    return msg

# ==========================
# MAIN HANDLER
# ==========================

def handle_message(phone: str, message: str) -> str:
    message = message.strip().lower()
    db: Session = SessionLocal()

    try:
        # --------------------------
        # RESET
        # --------------------------
        if message in {"hi", "hello", "start", "restart"}:
            booking = Booking(phone=phone, step=1)
            db.add(booking)
            db.commit()
            return "👋 Hi! May I have your name?"

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

        # --------------------------
        # STEP 1: NAME
        # --------------------------
        if booking.step == 1:
            booking.name = message.title()
            booking.step = 2
            db.commit()
            return f"Nice to meet you, {booking.name}! Which city is your hotel in?"

        # --------------------------
        # STEP 2: CITY
        # --------------------------
        if booking.step == 2:
            booking.location = message.title()
            booking.step = 3
            db.commit()
            return (
                "When do you want to check in?\n"
                "1️⃣ Tomorrow\n"
                "2️⃣ Day after tomorrow\n"
                "3️⃣ Other"
            )

        # --------------------------
        # STEP 3: CHECK-IN SELECTION
        # --------------------------
        if booking.step == 3:
            today = datetime.today().date()

            if message == "1":
                booking.checkin = (today + timedelta(days=1)).isoformat()
            elif message == "2":
                booking.checkin = (today + timedelta(days=2)).isoformat()
            elif message == "3":
                booking.step = 31
                db.commit()
                return "Please enter your check-in date (YYYY-MM-DD)"
            else:
                return "❌ Please reply with 1, 2, or 3."

            booking.step = 4
            db.commit()

        # --------------------------
        # STEP 31: MANUAL CHECK-IN
        # --------------------------
        if booking.step == 31:
            try:
                date = datetime.strptime(message, "%Y-%m-%d").date()
                if date < datetime.today().date():
                    return "❌ Check-in date cannot be in the past."

                booking.checkin = date.isoformat()
                booking.step = 4
                db.commit()
            except ValueError:
                return "❌ Please use YYYY-MM-DD format."

        # --------------------------
        # STEP 4: HISTORY / RECOMMENDATION
        # --------------------------
        if booking.step == 4:
            emp = get_employee(booking.name)

            if emp is not None:
                prev = get_previous_good_hotel(emp["employee_id"], booking.location)

                if prev is not None:
                    booking.step = 41
                    db.commit()
                    return (
                        f"You previously stayed at *{prev['hotel_name']}* "
                        f"(₹{prev[PRICE_COL]}/night).\n\n"
                        "Would you like to book this hotel again?\n"
                        "1️⃣ Yes\n"
                        "2️⃣ Show other options"
                    )

                booking.step = 42
                db.commit()
                return build_recommendation_text(
                    booking.location,
                    emp["price_cap_per_night"]
                )

            booking.step = 42
            db.commit()
            return build_recommendation_text(booking.location)

        # --------------------------
        # STEP 41: REUSE HOTEL
        # --------------------------
        if booking.step == 41:
            if message == "1":
                booking.step = 5
                db.commit()
                return "Great choice! What is your check-out date? (YYYY-MM-DD)"

            if message == "2":
                emp = get_employee(booking.name)
                cap = emp["price_cap_per_night"] if emp is not None else None
                booking.step = 42
                db.commit()
                return build_recommendation_text(booking.location, cap)

            return "❌ Please reply with 1 or 2."

        # --------------------------
        # STEP 42: HOTEL SELECTION
        # --------------------------
        if booking.step == 42:
            if not message.isdigit():
                return "❌ Please reply with the hotel number."

            choice = int(message)
            if choice not in {1, 2, 3}:
                return "❌ Please select a valid hotel number (1, 2, or 3)."

            booking.step = 5
            db.commit()
            return "Great choice! What is your check-out date? (YYYY-MM-DD)"

        # --------------------------
        # STEP 5: CHECK-OUT
        # --------------------------
        if booking.step == 5:
            try:
                checkout = datetime.strptime(message, "%Y-%m-%d").date()
                checkin = datetime.fromisoformat(booking.checkin).date()

                if checkout <= checkin:
                    return "❌ Check-out must be after check-in."

                booking.checkout = checkout.isoformat()
                booking.step = 6
                db.commit()

                return (
                    "✅ Booking confirmed!\n\n"
                    f"📍 City: {booking.location}\n"
                    f"📅 Check-in: {booking.checkin}\n"
                    f"📅 Check-out: {booking.checkout}\n\n"
                    "Type *Hi* to book again."
                )

            except ValueError:
                return "❌ Please use YYYY-MM-DD format."

        return "Type *Hi* to start a new booking."

    finally:
        db.close()
