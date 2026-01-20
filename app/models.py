from sqlalchemy import Column, Integer, String, DateTime
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
    created_at = Column(DateTime, default=datetime.utcnow)
