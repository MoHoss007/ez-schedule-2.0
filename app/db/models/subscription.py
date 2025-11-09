from __future__ import annotations
from sqlalchemy import (
    Column,
    Enum,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base
from db.utils import now_utc
from typing import Optional
from app.db.session import get_session
import enum


class SubscriptionStatus(enum.Enum):
    active = "active"
    canceled = "canceled"
    past_due = "past_due"
    incomplete = "incomplete"
    trialing = "trialing"
    unpaid = "unpaid"


class Subscription(Base):
    __tablename__ = "subscriptions"

    subscription_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True)

    stripe_customer_id = Column(String(255), nullable=False)
    stripe_subscription_id = Column(String(255), nullable=False, unique=True)

    current_teams = Column(Integer, nullable=False, default=1)
    future_teams = Column(Integer, nullable=False, default=1)

    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus),
        default=SubscriptionStatus.active,
        nullable=False,
        index=True,
    )
    current_period_end = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=now_utc)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="subscription")
