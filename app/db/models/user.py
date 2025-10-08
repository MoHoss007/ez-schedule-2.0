from __future__ import annotations
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship, declarative_base
from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    clubs = relationship("Club", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} email={self.email!r}>"
