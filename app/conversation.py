from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Booking
import pandas as pd
import os
import json

# ==========================
# LOAD CSV DATA
# ==========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

employees_df = pd.read_csv(os.path.join(DATA_DIR, "employees.csv"))
hotels_df = pd.read_csv(os.path.join(DATA_DIR, "hotels.csv"))
booking_history_df = pd.read_csv(os.path.join(DATA_DIR, "booking_history.csv"))

employees_df.columns = employees_df.columns.str.lower()
hotels_df.columns = hotels_df.columns.str.lower()
booking_history_df.columns = booking_history_df.columns.str.lower()

PRICE_COL = next(c for c in hotels_df.columns if c in {
    "price_per_night", "price", "room_price", "rate"
})

# ==========================
# HELPERS
# ==========================

def get_employee(name):
    df = employees_df[employees_df["employee_name"].str.lower() == name.lower()]
    return None if df.empty else df.iloc[0]


def get_previous_good_hotel(employee_id, city):
    history = booking_history_df[
        (booking_history_df["employee_id"] == employee_id) &
        (booking_history_df["city"].str.lower() == city.lower())
    ]

    if history.empty:
        return None

    last = history.iloc[-1]
    hotel = hotels_df[hotels_df["hotel_id"] == last["hotel_id"]].iloc[0]

    return {
        "hotel_name": hotel["hotel_name"],
        "price": int(hotel[PRICE_COL])
    }


def recommend_hotels(city, price_cap=None):
    df = hotels_df[hotels_df["city"].str.lower() == city.lower()]
    if price_cap is not None:
        df = df[df[PRICE_COL] <= price_cap]

    return df.sort_values(
        ["star_rating", PRICE_COL],
        ascending=[False, True]
    ).head(3)


def build_recommendation_text(df):
    msg = "Here are some recommended hotels:\n"
    for i, row in enumerate(df.itertuples(), 1):
        msg += f"{i}️⃣ {row.hotel_name} – ₹{getattr(row, PRICE_COL)}/night ⭐{row.star_rating}\n"
    msg += "\nReply with the hotel number."
    return msg

# ==========================
# MAIN HANDLER
# ==========================

def handle_message(phone: str, message: str) -> str:
    message = message.strip().lower()
    db: Session = SessionLocal()

    try:
        # RESET
        if message in {"hi", "hello", "start"}:
            booking = Booking(phone=phone, step=1)
            db.add(booking)
            db.commit()
            return "👋 Hi! May I have your name?"

        booking = db.query(Booking).filter(
            Booking.phone == phone
        ).order_by(Booking.id.desc()).first()

        if not booking:
            booking = Booking(phone=phone, step=1)
            db.add(booking)
            db.commit()
            return "May I have your name?"

        # STEP 1: NAME
        if booking.step == 1:
            booking.name = message.title()
            booking.step = 2
            db.commit()
            return f"Nice to meet you, {booking.name}! Which city is your hotel in?"

        # STEP 2: CITY
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

        # STEP 3: CHECK-IN
        if booking.step == 3:
            today = datetime.today().date()
            if message == "1":
                booking.checkin = (today + timedelta(days=1)).isoformat()
            elif message == "2":
                booking.checkin = (today + timedelta(days=2)).isoformat()
            elif message == "3":
                booking.step = 31
                db.commit()
                return "Enter check-in date (YYYY-MM-DD)"
            else:
                return "Reply with 1, 2, or 3."

            booking.step = 4
            db.commit()

        # STEP 31: MANUAL DATE
        if booking.step == 31:
            try:
                booking.checkin = datetime.strptime(message, "%Y-%m-%d").date().isoformat()
                booking.step = 4
                db.commit()
            except ValueError:
                return "Invalid date format."

        # STEP 4: HISTORY / RECOMMEND
        if booking.step == 4:
            emp = get_employee(booking.name)

            if emp is not None:
                prev = get_previous_good_hotel(emp["employee_id"], booking.location)
                if prev:
                    booking.selected_hotel = prev["hotel_name"]
                    booking.selected_price = prev["price"]
                    booking.step = 41
                    db.commit()
                    return (
                        f"You previously stayed at *{prev['hotel_name']}* "
                        f"(₹{prev['price']}/night).\n\n"
                        "1️⃣ Yes\n2️⃣ Show other options"
                    )

                recs = recommend_hotels(booking.location, emp["price_cap_per_night"])
            else:
                recs = recommend_hotels(booking.location)

            booking.recommendations = recs.to_json()
            booking.step = 45
            db.commit()
            return build_recommendation_text(recs)

        # STEP 41: REUSE HOTEL
        if booking.step == 41:
            if message == "1":
                booking.step = 5
                db.commit()
                return "What is your check-out date? (YYYY-MM-DD)"
            if message == "2":
                recs = recommend_hotels(booking.location)
                booking.recommendations = recs.to_json()
                booking.step = 45
                db.commit()
                return build_recommendation_text(recs)

        # STEP 45: HOTEL SELECTION
        if booking.step == 45:
            recs = pd.read_json(booking.recommendations)
            idx = int(message) - 1

            if idx < 0 or idx >= len(recs):
                return "Invalid hotel number."

            hotel = recs.iloc[idx]
            booking.selected_hotel = hotel["hotel_name"]
            booking.selected_price = int(hotel[PRICE_COL])
            booking.step = 5
            db.commit()
            return "What is your check-out date? (YYYY-MM-DD)"

        # STEP 5: CHECK-OUT
        if booking.step == 5:
            checkout = datetime.strptime(message, "%Y-%m-%d").date()
            booking.checkout = checkout.isoformat()
            booking.step = 6
            db.commit()

            return (
                "✅ Booking confirmed!\n\n"
                f"🏨 Hotel: {booking.selected_hotel}\n"
                f"💰 Price: ₹{booking.selected_price}/night\n"
                f"📍 City: {booking.location}\n"
                f"📅 {booking.checkin} → {booking.checkout}\n\n"
                "Type *Hi* to book again."
            )

        return "Type Hi to start again."

    finally:
        db.close()
