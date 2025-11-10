# migrator/lambda_migrator.py
import json, os, logging
from pathlib import Path

from alembic import command
from alembic.config import Config

log = logging.getLogger()
if not log.handlers:
    logging.basicConfig(level=logging.INFO)
log.setLevel(logging.INFO)

# Name of your Secrets Manager secret that contains {"DATABASE_URL": "..."}
SECRET_ID = os.getenv("SECRET_ID", "myapp/prod/db")

ALEMBIC_DIR = Path("/var/task/alembic")
ALEMBIC_INI = Path("/var/task/alembic.ini")


def _get_database_url() -> str:
    # Allow override by env var (handy for testing)
    url = os.getenv("DATABASE_URL")
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


def lambda_handler(event, context):
    """
    Event (optional):
      { "action": "upgrade" | "stamp" | "downgrade", "revision": "head" | "<rev>" | "-1" }
    Defaults: {"action":"upgrade","revision":"head"}
    """
    action = (event or {}).get("action", "upgrade")
    revision = (event or {}).get("revision", "head")

    db_url = _get_database_url()
    cfg = _alembic_config(db_url)

    log.info("Alembic %s -> %s", action, revision)
    if action == "upgrade":
        command.upgrade(cfg, revision)
    elif action == "downgrade":
        command.downgrade(cfg, revision)
    elif action == "stamp":
        command.stamp(cfg, revision)
    else:
        raise ValueError(f"Unsupported action: {action}")

    return {"ok": True, "action": action, "revision": revision}
