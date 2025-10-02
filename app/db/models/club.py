from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session
from app.db.base import Base
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Club(Base):
    __tablename__ = "clubs"

    club_id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(255), nullable=False)
    club_name = Column(String(255), nullable=False)

    def __repr__(self):
        return f"<Club(club_id={self.club_id}, club_name='{self.club_name}')>"

    @classmethod
    def get_token_by_name(cls, session: Session, club_name: str):
        club = session.query(cls).filter_by(club_name=club_name).first()
        return club.token if club else None

    @classmethod
    def get_club_by_name(cls, session: Session, club_name: str):
        return session.query(cls).filter_by(club_name=club_name).first()
