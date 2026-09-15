import sqlite3
from pathlib import Path

from backend.core.config import get_settings

_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def connect() -> sqlite3.Connection:
    path = Path(get_settings().db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def migrate(conn: sqlite3.Connection) -> list[str]:
    """Apply backend/migrations/*.sql in filename order; returns names applied."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS _migrations ("
        " name TEXT PRIMARY KEY,"
        " applied_at TEXT NOT NULL DEFAULT (datetime('now')))"
    )
    applied = {row["name"] for row in conn.execute("SELECT name FROM _migrations")}
    ran: list[str] = []
    for file in sorted(_MIGRATIONS_DIR.glob("*.sql")):
        if file.name in applied:
            continue
        conn.executescript(file.read_text(encoding="utf-8"))
        conn.execute("INSERT INTO _migrations (name) VALUES (?)", (file.name,))
        conn.commit()
        ran.append(file.name)
    return ran
