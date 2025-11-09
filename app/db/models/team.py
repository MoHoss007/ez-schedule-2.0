from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session
from app.db.base import Base
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Team(Base):
    __tablename__ = "teams"

    team_id = Column(Integer, primary_key=True, autoincrement=True)
    club_id = Column(ForeignKey("clubs.club_id"), nullable=False)

    team_name = Column(String(255), nullable=False)
    home_kit = Column(String(255), nullable=True)
    away_kit = Column(String(255), nullable=True)
    teamsnap_team_id = Column(String(255), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship to Club (optional)
    club = relationship("Club", backref="teams")

    def __repr__(self):
        return f"<Team(team_id={self.team_id}, team_name='{self.team_name}', club_id={self.club_id}, teamsnap_id={self.teamsnap_id})>"

    @classmethod
    def get_teams_by_club_id(cls, session: Session, club_id: int):
        return session.query(cls).filter_by(club_id=club_id).all()
