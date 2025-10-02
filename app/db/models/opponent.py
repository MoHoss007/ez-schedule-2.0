from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Opponent(Base):
    __tablename__ = "opponents"

    opponent_id = Column(Integer, primary_key=True, autoincrement=True)  # manually set
    name = Column(String(255), nullable=False)

    contacts_name = Column(String(255), nullable=True)
    contacts_phone = Column(String(50), nullable=True)
    contacts_email = Column(String(255), nullable=True)

    team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    team = relationship("Team", backref="opponents")

    teamsnap_opponent_id = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<Opponent(opponent_id={self.opponent_id}, name='{self.name}', team_id={self.team_id}, teamsnap_opponent_id={self.teamsnap_opponent_id})>"

    @classmethod
    def get_or_create(
        cls,
        session: Session,
        name: str,
        team_id: int,
        contacts_name: Optional[str] = None,
        contacts_phone: Optional[str] = None,
        contacts_email: Optional[str] = None,
        teamsnap_opponent_id: Optional[str] = None,
    ):
        existing = (
            session.query(cls)
            .filter((cls.name == name), (cls.team_id == team_id))
            .first()
        )
        if existing:
            return existing
        opponent = cls(
            name=name,
            team_id=team_id,
            contacts_name=contacts_name,
            contacts_phone=contacts_phone,
            contacts_email=contacts_email,
            teamsnap_opponent_id=teamsnap_opponent_id,
        )
        session.add(opponent)
        session.flush()
        session.refresh(opponent)
        return opponent

    @classmethod
    def get_opponents(cls, session: Session, team_id: int) -> Optional[List]:
        """
        Retrieves a list of opponents for a specific team that do not have a Teamsnap ID.

        Args:
            team_id (int): ID of the team to check against
            teamsnap_opponent_id (str): Optional Teamsnap opponent ID to filter by

        Returns:
            list: List of Opponent objects if found, empty list otherwise
        """
        opponents = (
            session.query(cls)
            .filter(cls.team_id == team_id, cls.teamsnap_opponent_id == None)
            .all()
        )
        if opponents:
            return opponents

    @classmethod
    def update_opponent(
        cls, session: Session, opponent_id: int, teamsnap_opponent_id: str, team_id: int
    ) -> bool:
        db_opponent = (
            session.query(cls)
            .filter(cls.opponent_id == opponent_id, cls.team_id == team_id)
            .first()
        )
        if db_opponent:
            db_opponent.teamsnap_opponent_id = teamsnap_opponent_id
            logger.info(f"Successfully updated opponent: {db_opponent}")
            return True
        return False
