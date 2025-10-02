from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Location(Base):
    __tablename__ = "locations"

    location_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    address = Column(String(512), nullable=False)
    url = Column(String(512), nullable=True)
    teamsnap_location_id = Column(String(255), nullable=True)

    team_id = Column(Integer, ForeignKey("teams.team_id"), nullable=False)
    team = relationship("Team", backref="locations")

    def __repr__(self):
        return f"<Location(location_id={self.location_id}, name='{self.name}', teamsnap_location_id={self.teamsnap_location_id})>"

    @classmethod
    def get_or_create(
        cls,
        session: Session,
        name: str,
        address: str,
        team_id: int,
        url: Optional[str] = None,
        teamsnap_location_id: Optional[str] = None,
    ):
        existing = (
            session.query(cls)
            .filter(
                (cls.name == name) | (cls.address == address) | (cls.url == url),
                cls.team_id == team_id,
            )
            .first()
        )
        if existing:
            return existing
        location = cls(
            name=name,
            address=address,
            team_id=team_id,
            url=url,
            teamsnap_location_id=teamsnap_location_id,
        )
        session.add(location)
        session.flush()
        session.refresh(location)
        return location

    @classmethod
    def get_locations(cls, session: Session, team_id: int) -> Optional[List]:
        """
        Retrieves a list of locations for a specific team that do not have a Teamsnap ID.

        Args:
            team_id (int): ID of the team to check against
            teamsnap_location_id (str): Optional Teamsnap opponent ID to filter by

        Returns:
            list: List of Opponent objects if found, empty list otherwise
        """

        locations = (
            session.query(cls)
            .filter(cls.team_id == team_id, cls.teamsnap_location_id == None)
            .all()
        )
        if locations:
            return locations

    @classmethod
    def update_location(
        cls, session: Session, location_id: int, teamsnap_location_id: str, team_id: int
    ) -> bool:
        db_location = (
            session.query(cls)
            .filter(cls.location_id == location_id, cls.team_id == team_id)
            .first()
        )
        if db_location:
            db_location.teamsnap_location_id = teamsnap_location_id
            logger.info(f"Successfully updated location: {db_location}")
            return True
        return False
