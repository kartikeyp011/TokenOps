"""
Database setup — SQLAlchemy engine, session factory, and Base.
All ORM models import Base from here.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# SQLite-specific: enable WAL mode and foreign keys
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # required for SQLite + FastAPI
    echo=settings.debug,                         # logs SQL in debug mode
)

# Enable WAL mode for better concurrent read performance
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """Create all tables. Called on app startup."""
    from app.models import db_models  # noqa: F401 — import triggers table registration
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    FastAPI dependency — yields a DB session per request.
    Session is closed automatically after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()