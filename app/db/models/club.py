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
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from app.db.utils import now_utc
from app.db.base import Base
from enum import Enum


class Club(Base):
    __tablename__ = "clubs"

    club_id = Column(Integer, primary_key=True, autoincrement=True)

    owner_id = Column(
        Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )

    league_id = Column(
        Integer,
        ForeignKey("leagues.league_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    display_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    owner = relationship("User", back_populates="clubs")
    league = relationship("League", back_populates="clubs")

    teams = relationship(
        "Team",
        back_populates="club",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    club_integrations = relationship(
        "ClubIntegration",
        back_populates="club",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Club id={self.club_id} name={self.display_name!r}>"


class Team(Base):
    __tablename__ = "teams"

    team_id = Column(Integer, primary_key=True, autoincrement=True)

    club_id = Column(
        Integer,
        ForeignKey("clubs.club_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    club = relationship("Club", back_populates="teams")

    team_integrations = relationship(
        "TeamIntegration",
        back_populates="team",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Team id={self.team_id} name={self.name!r} club_id={self.club_id}>"


# =========================================
#  INTEGRATION PROVIDERS + ACCOUNTS
# =========================================


class AuthType(Enum):
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    OTHER = "other"


class IntegrationProvider(Base):
    __tablename__ = "integration_providers"

    provider_id = Column(Integer, primary_key=True, autoincrement=True)

    code = Column(String(64), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)

    auth_type = Column(SAEnum(AuthType), nullable=False, default=AuthType.OAUTH2)  # type: ignore

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)

    integration_accounts = relationship(
        "IntegrationAccount",
        back_populates="provider",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<IntegrationProvider id={self.provider_id} code={self.code!r}>"


class IntegrationAccount(Base):
    """
    Represents a user's connected account with a given provider (e.g. TeamSnap).
    Holds tokens for API calls.
    """

    __tablename__ = "integration_accounts"

    integration_account_id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provider_id = Column(
        Integer,
        ForeignKey("integration_providers.provider_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    external_user_id = Column(String(255), nullable=False)  # e.g. provider /me id
    scope = Column(String(512), nullable=True)

    access_token_enc = Column(String(2048), nullable=False)
    refresh_token_enc = Column(String(2048), nullable=True)
    access_token_expires_at = Column(DateTime(timezone=True), nullable=False)

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)

    user = relationship("User", back_populates="integration_accounts")
    provider = relationship(
        "IntegrationProvider", back_populates="integration_accounts"
    )

    club_integrations = relationship(
        "ClubIntegration",
        back_populates="integration_account",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "provider_id",
            "external_user_id",
            name="uq_integration_account_user_provider_external",
        ),
        Index(
            "ix_integration_accounts_provider_external",
            "provider_id",
            "external_user_id",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<IntegrationAccount id={self.integration_account_id} "
            f"user_id={self.user_id} provider={self.provider_id}>"
        )


# =========================================
#  CLUB / TEAM INTEGRATION MAPPINGS
# =========================================


class ClubIntegration(Base):
    """
    Mapping between an ez-schedule Club and a provider-specific club/org.
    """

    __tablename__ = "club_integrations"

    id = Column(Integer, primary_key=True, autoincrement=True)

    club_id = Column(
        Integer,
        ForeignKey("clubs.club_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    integration_account_id = Column(
        Integer,
        ForeignKey("integration_accounts.integration_account_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    external_club_id = Column(String(255), nullable=False)
    external_name = Column(String(255), nullable=True)
    external_raw = Column(JSON, nullable=True)  # snapshot of provider response

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)

    club = relationship("Club", back_populates="club_integrations")
    integration_account = relationship(
        "IntegrationAccount", back_populates="club_integrations"
    )

    team_integrations = relationship(
        "TeamIntegration",
        back_populates="club_integration",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "integration_account_id",
            "external_club_id",
            name="uq_club_integration_external",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ClubIntegration club_id={self.club_id} "
            f"external_club_id={self.external_club_id!r}>"
        )


class TeamIntegration(Base):
    """
    Mapping between an ez-schedule Team and a provider-specific team.
    """

    __tablename__ = "team_integrations"

    id = Column(Integer, primary_key=True, autoincrement=True)

    team_id = Column(
        Integer,
        ForeignKey("teams.team_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    club_integration_id = Column(
        Integer,
        ForeignKey("club_integrations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    external_team_id = Column(String(255), nullable=False)
    external_name = Column(String(255), nullable=True)
    external_raw = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)

    team = relationship("Team", back_populates="team_integrations")
    club_integration = relationship(
        "ClubIntegration", back_populates="team_integrations"
    )

    __table_args__ = (
        UniqueConstraint(
            "club_integration_id",
            "external_team_id",
            name="uq_team_integration_external",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<TeamIntegration team_id={self.team_id} "
            f"external_team_id={self.external_team_id!r}>"
        )


# =========================================
#  OAUTH STATE (FOR INTEGRATION FLOWS)
# =========================================


class OAuthState(Base):
    """
    Generic OAuth state for redirect/PKCE flows with any provider.
    """

    __tablename__ = "oauth_states"

    # random opaque token, treat as string
    id = Column(String(128), primary_key=True)

    provider_id = Column(
        Integer,
        ForeignKey("integration_providers.provider_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    code_verifier = Column(String(256), nullable=True)

    # You can store arbitrary “draft” info like club display name, league_id, redirect target, etc.
    draft_payload = Column(JSON, nullable=True)

    provider = relationship("IntegrationProvider")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<OAuthState id={self.id!r} provider_id={self.provider_id} user_id={self.user_id}>"
