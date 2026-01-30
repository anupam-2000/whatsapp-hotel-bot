from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.db import Base

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, index=True)

    name = Column(String)
    location = Column(String)

    checkin = Column(String)
    checkout = Column(String)

    step = Column(Integer, default=1)

    # ✅ NEW FIELDS
    selected_hotel = Column(String, nullable=True)
    selected_price = Column(Integer, nullable=True)
    recommendations = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
