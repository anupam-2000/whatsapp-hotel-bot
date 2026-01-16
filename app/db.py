from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# SQLite database path
DATABASE_URL = "sqlite:///./data/bookings.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()

# IMPORTANT: Import models so SQLAlchemy knows them
from app.models import Booking  # noqa: E402

# Create tables automatically
Base.metadata.create_all(bind=engine)
