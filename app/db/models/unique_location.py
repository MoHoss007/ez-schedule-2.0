from __future__ import annotations
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session
from app.db.base import Base
from typing import Optional
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class UniqueLocation(Base):
    __tablename__ = "unique_locations"

    location_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    address = Column(String(512), nullable=False)
    url = Column(String(512), nullable=True)

    def __repr__(self):
        return f"<Location(location_id={self.location_id}, name='{self.name}')>"

    @classmethod
    def get_or_create(
        cls,
        session: Session,
        name: str,
        address: str,
        url: Optional[str] = None,
    ) -> UniqueLocation:
        existing = (
            session.query(cls)
            .filter((cls.name == name) | (cls.address == address) | (cls.url == url))
            .first()
        )
        if existing:
            return existing
        location = cls(name=name, address=address, url=url)
        session.add(location)
        session.flush()
        session.refresh(location)
        return location

    @classmethod
    def get_by_name(cls, session: Session, name: str) -> Optional[UniqueLocation]:
        return session.query(cls).filter(cls.name == name).first()
