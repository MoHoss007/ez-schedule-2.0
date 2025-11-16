import json, os, logging
from pathlib import Path

from alembic import command
from alembic.config import Config

# NEW: import SQLAlchemy for querying
from sqlalchemy import create_engine, text

log = logging.getLogger()
if not log.handlers:
    logging.basicConfig(level=logging.INFO)
log.setLevel(logging.INFO)

SECRET_ID = os.getenv("SECRET_ID", "myapp/prod/db")

ALEMBIC_DIR = Path("/var/task/alembic")
ALEMBIC_INI = Path("/var/task/alembic.ini")


def _get_database_url() -> str:
    # Allow override by env var (handy for testing)
    url = os.getenv("EZ_SCHEDULE_DB_URI")
    if url:
        return url
    raise RuntimeError("DATABASE_URL not found in secret")


def _alembic_config(db_url: str) -> Config:
    if not ALEMBIC_DIR.exists():
        raise RuntimeError(f"Missing alembic/ at {ALEMBIC_DIR}")
    if not ALEMBIC_INI.exists():
        raise RuntimeError(f"Missing alembic.ini at {ALEMBIC_INI}")
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(ALEMBIC_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg

def _inspect_tables(db_url: str):
    """Prints all table names in the database."""
    print("=== [INSPECT] Connecting to DB ===")
    engine = create_engine(db_url)

    with engine.connect() as conn:
        print("=== [INSPECT] SHOW TABLES ===")
        result = conn.execute(text("SHOW TABLES"))
        for row in result:
            # Row is like: ('users',)
            print(f"- {row[0]}")

def _inspect_alembic_version(db_url: str):
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("=== [INSPECT] alembic_version ===")
        try:
            rows = conn.execute(text("SELECT version_num FROM alembic_version"))
            for row in rows:
                print(f"- version_num: {row[0]}")
        except Exception as e:
            print(f"Error reading alembic_version: {e}")

def lambda_handler(event, context):
    """
    Event (optional):
      { "action": "upgrade" | "stamp" | "downgrade" | "inspect",
        "revision": "head" | "<rev>" | "-1",
        "table": "users",
        "limit": 10
      }

    Defaults: {"action":"upgrade","revision":"head"}
    """
    event = event or {}
    action = event.get("action", "upgrade")
    revision = event.get("revision", "head")

    db_url = _get_database_url()

    # Alembic-related actions
    if action in ("upgrade", "downgrade", "stamp"):
        cfg = _alembic_config(db_url)
        log.info("Alembic %s -> %s", action, revision)
        if action == "upgrade":
            command.upgrade(cfg, revision)
        elif action == "downgrade":
            command.downgrade(cfg, revision)
        elif action == "stamp":
            command.stamp(cfg, revision)
        return {"ok": True, "action": action, "revision": revision}

    # NEW: inspect action
    if action == "inspect":
        _inspect_alembic_version(db_url)
        _inspect_tables(db_url)
        return {"ok": True, "action": action}

    # Unknown action
    raise ValueError(f"Unsupported action: {action}")
