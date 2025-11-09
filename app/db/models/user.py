from __future__ import annotations
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship, declarative_base
from typing import Optional
from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    clubs = relationship(
        "Club",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<User user_id={self.user_id} email={self.email!r}>"
