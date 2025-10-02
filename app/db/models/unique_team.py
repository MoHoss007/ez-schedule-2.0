from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String
from app.db.base import Base
import logging
from sqlalchemy import ForeignKey

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class UniqueTeam(Base):
    __tablename__ = "unique_teams"

    team_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    division_id = Column(
        Integer, ForeignKey("unique_divisions.division_id"), nullable=False
    )

    def __repr__(self):
        return f"<Team(team_id={self.team_id}, name='{self.name}', division_id={self.division_id})>"

    @classmethod
    def get_or_create(cls, session: Session, name: str, division_id: int) -> int:
        instance = (
            session.query(cls).filter_by(name=name, division_id=division_id).first()
        )
        if instance:
            return instance.team_id  # type: ignore
        instance = cls(name=name, division_id=division_id)
        session.add(instance)
        session.flush()
        return instance.team_id  # type: ignore
