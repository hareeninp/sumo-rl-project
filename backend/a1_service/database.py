"""
database.py - SQLite persistence for A1 (login/role service + closures + incidents).

SQLite chosen per team decision: zero setup, real persistence across restarts,
trivial swap to Postgres later if ever needed. File lives alongside this module
so it survives server restarts during demo rehearsal.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_PATH = os.path.join(os.path.dirname(__file__), "a1_service.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
