from __future__ import annotations

from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Index,
    Enum as SAEnum,
    JSON,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.utils import now_utc
from enum import Enum


class League(Base):
    __tablename__ = "leagues"

    league_id = Column(Integer, primary_key=True, autoincrement=True)

    name = Column(String(255), nullable=False)
    code = Column(String(64), nullable=False, unique=True, index=True)
    timezone = Column(String(64), nullable=False, default="America/Toronto")
    age_group = Column(String(64), nullable=True)
    division = Column(String(64), nullable=True)

    created_at = Column(DateTime(timezone=True), default=now_utc(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    league_seasons = relationship(
        "LeagueSeason",
        back_populates="league",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    clubs = relationship("Club", back_populates="league")

    def __repr__(self) -> str:
        return f"<League id={self.league_id} code={self.code!r}>"


class LeagueSeason(Base):
    __tablename__ = "league_seasons"

    league_season_id = Column(Integer, primary_key=True, autoincrement=True)

    league_id = Column(
        Integer,
        ForeignKey("leagues.league_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String(255), nullable=False)  # e.g. "2025 Summer"

    season_start = Column(DateTime(timezone=True), nullable=False)
    season_end = Column(DateTime(timezone=True), nullable=False)

    # When users can start/stop buying new subscriptions for this season
    subscription_open_at = Column(DateTime(timezone=True), nullable=False)
    subscription_close_at = Column(DateTime(timezone=True), nullable=False)

    # Deadline for changing team_limit for this season
    change_deadline_for_current = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=now_utc(), nullable=False)

    league = relationship("League", back_populates="league_seasons")

    products = relationship(
        "LeagueSeasonProduct",
        back_populates="league_season",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    subscriptions = relationship(
        "Subscription",
        back_populates="league_season",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_league_seasons_league_id", "league_id"),
        Index("ix_league_seasons_start_end", "season_start", "season_end"),
    )

    def __repr__(self) -> str:
        return f"<LeagueSeason id={self.league_season_id} name={self.name!r}>"


class PricingModel(Enum):
    PER_TEAM = "per_team"
    FLAT = "flat"


class LeagueSeasonProduct(Base):
    """
    Optional table that maps a league season to Stripe prices / pricing model.
    """

    __tablename__ = "league_season_products"

    id = Column(Integer, primary_key=True, autoincrement=True)

    league_season_id = Column(
        Integer,
        ForeignKey("league_seasons.league_season_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    stripe_price_id = Column(String(255), nullable=False, unique=True, index=True)
    pricing_model = Column(SAEnum(PricingModel), nullable=False)
    product_metadata = Column(JSON, nullable=True)

    league_season = relationship("LeagueSeason", back_populates="products")

    def __repr__(self) -> str:
        return f"<LeagueSeasonProduct id={self.id} stripe_price_id={self.stripe_price_id!r}>"
