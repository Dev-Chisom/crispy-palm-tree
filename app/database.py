"""Database connection and session management."""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create database engine with memory-efficient pool settings
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,  # Reduced for Railway/memory efficiency
    max_overflow=10,  # Reduced for Railway/memory efficiency
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False,  # Disable SQL logging to save memory
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()




def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
