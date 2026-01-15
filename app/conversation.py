import pandas as pd
from datetime import datetime
import os

FILE_PATH = "data/bookings.xlsx"

def load_data():
    if os.path.exists(FILE_PATH):
        return pd.read_excel(FILE_PATH)
    else:
        return pd.DataFrame(columns=[
            "phone", "name", "checkin", "checkout", "step"
        ])

def save_data(df):
    os.makedirs("data", exist_ok=True)
    df.to_excel(FILE_PATH, index=False)

def handle_message(phone, message):
    message = message.strip()
    df = load_data()

    if phone not in df["phone"].values:
        # New user
        df = pd.concat([df, pd.DataFrame([{
            "phone": phone,
            "name": None,
            "checkin": None,
            "checkout": None,
            "step": 1
        }])], ignore_index=True)
        save_data(df)
        return "May I have your name?"

    user = df[df["phone"] == phone].iloc[0]
    idx = df[df["phone"] == phone].index[0]

    if user["step"] == 1:
        df.at[idx, "name"] = message
        df.at[idx, "step"] = 2
        save_data(df)
        return f"Nice to meet you, {message}! What is your check-in date? (YYYY-MM-DD)"

    if user["step"] == 2:
        try:
            datetime.strptime(message, "%Y-%m-%d")
            df.at[idx, "checkin"] = message
            df.at[idx, "step"] = 3
            save_data(df)
            return "Got it! What is your check-out date? (YYYY-MM-DD)"
        except ValueError:
            return "Please enter the check-in date in YYYY-MM-DD format."

    if user["step"] == 3:
        try:
            datetime.strptime(message, "%Y-%m-%d")
            df.at[idx, "checkout"] = message
            df.at[idx, "step"] = 4
            save_data(df)
            return "✅ Your booking request is saved! We’ll contact you shortly."
        except ValueError:
            return "Please enter the check-out date in YYYY-MM-DD format."

    return "Your booking is already completed. Type 'restart' to start again."
