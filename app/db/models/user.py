from __future__ import annotations
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Boolean, Index
from app.db.utils import now_utc
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)

    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)

    # Relationships
    sessions = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    subscriptions = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    clubs = relationship(
        "Club",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    integration_accounts = relationship(
        "IntegrationAccount",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User user_id={self.user_id} email={self.email!r}>"


class Session(Base):
    """
    Hybrid JWT + DB session:
    - access token is short-lived & stateless
    - refresh token is tied to this row via jti/hash
    """

    __tablename__ = "sessions"

    session_id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    last_seen_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Store only a hash of the refresh token (or jti)
    refresh_token_hash = Column(String(255), nullable=False)

    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)

    is_revoked = Column(Boolean, default=False, nullable=False, index=True)

    user = relationship("User", back_populates="sessions")

    __table_args__ = (Index("ix_sessions_user_id_is_revoked", "user_id", "is_revoked"),)

    def __repr__(self) -> str:
        return f"<Session session_id={self.session_id} user_id={self.user_id}>"
