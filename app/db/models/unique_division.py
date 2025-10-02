from __future__ import annotations
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session
from app.db.base import Base
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class UniqueDivision(Base):
    __tablename__ = "unique_divisions"

    division_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)

    def __repr__(self):
        return f"<Division(division_id={self.division_id}, name='{self.name}')>"

    @classmethod
    def get_or_create(cls, session: Session, name: str) -> int:
        instance = session.query(cls).filter_by(name=name).first()
        if instance:
            return instance.division_id  # type: ignore
        instance = cls(name=name)
        session.add(instance)
        session.flush()
        return instance.division_id  # type: ignore
