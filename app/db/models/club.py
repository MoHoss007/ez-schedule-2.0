# app/db/models.py
from __future__ import annotations
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone, timedelta
import uuid

Base = declarative_base()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Club(Base):
    __tablename__ = "clubs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True, index=True)

    # optional “display” info you might collect in draft (e.g., contact email)
    contact_email = Column(String(255), nullable=True)

    # relationship to TeamSnapAccount(s)
    teamsnap_accounts = relationship(
        "TeamSnapAccount", back_populates="club", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Club id={self.id} name={self.name!r}>"


class OAuthState(Base):
    __tablename__ = "oauth_state"
    id = Column(String(64), primary_key=True)  # random token_urlsafe
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    code_verifier = Column(String(255), nullable=False)

    # For draft club binding (what the UI collected before redirect)
    draft_club_payload = Column(
        JSON, nullable=True
    )  # e.g., {"name": "...", "contact_email": "..."}


class TeamSnapAccount(Base):
    __tablename__ = "teamsnap_accounts"
    id = Column(Integer, primary_key=True)
    club_id = Column(ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    teamsnap_user_id = Column(String(64), nullable=False)  # from TeamSnap /me
    scope = Column(String(512), nullable=True)

    # Encrypted-at-rest token fields
    access_token_enc = Column(String(2048), nullable=False)
    refresh_token_enc = Column(String(2048), nullable=True)
    access_token_expires_at = Column(DateTime(timezone=True), nullable=False)

    club = relationship("Club", back_populates="teamsnap_accounts")

    __table_args__ = (
        UniqueConstraint("club_id", "teamsnap_user_id", name="uq_club_teamsnapid"),
        Index("ix_teamsnap_user", "teamsnap_user_id"),
    )
