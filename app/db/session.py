from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from typing import Generator
from app.config import Config
import os

ENV = os.getenv("APP_ENV", "development")

if not Config.DB_URI:
    raise ValueError("Database URI is not set in the configuration.")

engine = create_engine(
    Config.DB_URI,
    echo=(ENV != "production"),
    pool_pre_ping=True,
)

SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()  # Each call gets a thread-local session
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
