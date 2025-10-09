# create_tables.py
from app.db.base import Base
from app.db.session import engine
from app.db.models import *


def create_all_tables():
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully.")


if __name__ == "__main__":
    create_all_tables()
