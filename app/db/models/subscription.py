from __future__ import annotations
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.utils import now_utc
from enum import Enum


class SubscriptionStatus(Enum):
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"


class Subscription(Base):
    """
    One subscription per (user, league_season).
    Controls number of teams the user can manage that season.
    """

    __tablename__ = "subscriptions"

    subscription_id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    league_season_id = Column(
        Integer,
        ForeignKey("league_seasons.league_season_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Stripe references
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    stripe_subscription_id = Column(String(255), nullable=True, unique=True, index=True)

    status = Column(
        SAEnum(SubscriptionStatus),  # type: ignore
        default=SubscriptionStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    # Number of teams allowed for this user's subscription in this season
    team_limit = Column(Integer, nullable=False)

    # How many teams were actually billed (freeze at invoice time if you want)
    billed_team_count = Column(Integer, nullable=True)

    # When billing is considered to start (usually season_start)
    billing_start_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)

    deleted_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="subscriptions")
    league_season = relationship("LeagueSeason", back_populates="subscriptions")

    team_changes = relationship(
        "SubscriptionTeamChange",
        back_populates="subscription",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "league_season_id", name="uq_user_league_season_subscription"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Subscription id={self.subscription_id} user_id={self.user_id} "
            f"league_season_id={self.league_season_id} team_limit={self.team_limit}>"
        )


class SubscriptionTeamChange(Base):
    """
    Optional history table for tracking changes to team_limit.
    """

    __tablename__ = "subscription_team_changes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    subscription_id = Column(
        Integer,
        ForeignKey("subscriptions.subscription_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    old_team_limit = Column(Integer, nullable=False)
    new_team_limit = Column(Integer, nullable=False)

    changed_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    changed_by_user_id = Column(
        Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )

    reason = Column(String(255), nullable=True)

    subscription = relationship("Subscription", back_populates="team_changes")
    changed_by = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<SubscriptionTeamChange sub_id={self.subscription_id} "
            f"{self.old_team_limit}->{self.new_team_limit}>"
        )
