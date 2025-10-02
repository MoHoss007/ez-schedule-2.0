from __future__ import annotations
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Event(Base):
    __tablename__ = "events"

    event_id = Column(Integer, primary_key=True, autoincrement=True)  # auto-generated
    team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    opponent_id = Column(Integer, ForeignKey("opponents.opponent_id"), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.location_id"), nullable=True)

    start_date = Column(DateTime, nullable=False)
    duration_in_minutes = Column(Integer, nullable=False)

    is_game = Column(Boolean, default=True)
    is_tbd = Column(Boolean, default=False)
    tracks_availability = Column(Boolean, default=False)

    browser_time_zone = Column(String(100), nullable=True)
    time_zone = Column(String(100), nullable=True)

    notify_team = Column(Boolean, default=False)
    notify_opponent = Column(Boolean, default=False)
    notify_opponent_contacts_name = Column(String(255), nullable=True)
    notify_opponent_contacts_email = Column(String(255), nullable=True)
    notify_team_as_member_id = Column(Integer, nullable=True)

    uploaded = Column(Boolean, nullable=False, default=False)  # new field
    updated = Column(Boolean, nullable=False, default=False)  # new field

    # Relationships
    team = relationship("Team", backref="events")
    opponent = relationship("Opponent", backref="events")
    location = relationship("Location", backref="events")

    teamsnap_event_id = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<Event(event_id={self.event_id}, team_id={self.team_id}, start_date={self.start_date})>"

    @classmethod
    def get_or_create(cls, session: Session, **kwargs) -> Optional[Event]:
        opponent_id = kwargs.get("opponent_id")
        location_id = kwargs.get("location_id")
        start_date = kwargs.get("start_date")
        existing_event = (
            session.query(cls)
            .filter_by(
                opponent_id=opponent_id,
                location_id=location_id,
                start_date=start_date,
            )
            .first()
        )
        if existing_event:
            return existing_event
        event = cls(**kwargs)
        session.add(event)
        session.refresh(event)
        return event

    @classmethod
    def get_not_uploaded(cls, session: Session, team_id: Optional[int] = None) -> List:
        if team_id is None:
            return session.query(cls).filter(cls.uploaded == False).all()
        return (
            session.query(cls)
            .filter(cls.uploaded == False, cls.team_id == team_id)
            .all()
        )

    @classmethod
    def update_uploaded_status(
        cls, session: Session, event_id: int, teamsnap_event_id: str
    ) -> bool:
        db_event = session.query(cls).filter(cls.event_id == event_id).first()
        if db_event:
            db_event.uploaded = True
            db_event.teamsnap_event_id = teamsnap_event_id
            logger.info(f"Successfully updated event: {db_event}")
            return True
        return False
