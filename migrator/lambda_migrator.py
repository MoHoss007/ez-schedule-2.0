import json, os, logging
from pathlib import Path

from alembic import command
from alembic.config import Config

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


def _drop_all_tables(db_url: str):
    """
    Drops ALL tables in the current database (including alembic_version).
    This is destructive. Use with care.
    """
    print("=== [RESET] Connecting to DB ===")
    engine = create_engine(db_url)

    # Use a transaction so we can commit all drops together
    with engine.begin() as conn:
        print("=== [RESET] Disabling foreign key checks ===")
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

        print("=== [RESET] Fetching tables ===")
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result]

        if not tables:
            print("=== [RESET] No tables found ===")
        else:
            print("=== [RESET] Dropping tables ===")
            for tbl in tables:
                print(f"- Dropping table: {tbl}")
                conn.execute(text(f"DROP TABLE IF EXISTS `{tbl}`"))

        print("=== [RESET] Re-enabling foreign key checks ===")
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

    print("=== [RESET] Done dropping all tables ===")

def _run_query(db_url: str, sql: str, params: dict | None = None, allow_write: bool = False):
    """
    Execute a SQL statement and print the results to CloudWatch logs.

    Event usage:
      {
        "action": "query",
        "sql": "SELECT * FROM users LIMIT 5",
        "params": {"user_id": 1},        # optional
        "allow_write": true              # required for INSERT/UPDATE/DELETE, etc.
      }
    """
    sql_stripped = sql.strip()
    first_word = sql_stripped.split()[0].lower() if sql_stripped else ""

    # Simple safety: by default only allow read-only queries
    read_only_starts = ("select", "show", "describe", "explain")
    if not allow_write and first_word not in read_only_starts:
        raise ValueError(
            "Refusing to run non-read-only query without allow_write=true. "
            f"First word was: {first_word!r}"
        )

    print("=== [QUERY] Connecting to DB ===")
    engine = create_engine(db_url)

    with engine.begin() as conn:
        print(f"=== [QUERY] SQL ===\n{sql_stripped}")
        if params:
            print(f"=== [QUERY] PARAMS === {params}")
        result = conn.execute(text(sql_stripped), params or {})

        if result.returns_rows:
            print("=== [QUERY] RESULT ROWS ===")
            for row in result:
                # row is a Row object; convert to tuple for clean printing
                print(tuple(row))
        else:
            print(f"=== [QUERY] ROWCOUNT === {result.rowcount}")



def lambda_handler(event, context):
    """
    Event (optional):
      {
        "action": "upgrade" | "stamp" | "downgrade" | "inspect" | "reset" | "query",
        "revision": "head" | "<rev>" | "-1",
        "confirm": "DROP_ALL_TABLES",   # optional safety for reset
        "sql": "...",                    # for query
        "params": { ... },               # optional for query
        "allow_write": true/false        # optional for query (default false)
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

    # Inspect action
    if action == "inspect":
        _inspect_alembic_version(db_url)
        _inspect_tables(db_url)
        return {"ok": True, "action": action}

    # reset action (drop all tables)
    if action == "reset":
        confirm = event.get("confirm")
        if confirm != "DROP_ALL_TABLES":
            raise ValueError("Refusing to reset DB without confirm='DROP_ALL_TABLES'")
        log.warning("RESET action requested: dropping all tables in database!")
        _drop_all_tables(db_url)
        return {"ok": True, "action": action}

    # NEW: arbitrary query action
    if action == "query":
        sql = event.get("sql")
        if not sql:
            raise ValueError("For action 'query', you must provide 'sql' in the event.")
        params = event.get("params") or {}
        allow_write = bool(event.get("allow_write", False))

        _run_query(db_url, sql, params=params, allow_write=allow_write)
        return {"ok": True, "action": action}

    # Unknown action
    raise ValueError(f"Unsupported action: {action}")

