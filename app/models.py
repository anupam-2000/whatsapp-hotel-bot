from sqlalchemy import Column, Integer, String, Date
from app.db import Base
from datetime import date

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, index=True)
    name = Column(String)
    location = Column(String)
    checkin = Column(String)
    checkout = Column(String)
    created_date = Column(Date, default=date.today)
    step = Column(Integer)
