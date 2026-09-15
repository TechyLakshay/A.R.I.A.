import sqlite3


def _fresh_conn(tmp_path, monkeypatch) -> sqlite3.Connection:
    monkeypatch.setenv("JARVIS_DB_PATH", str(tmp_path / "test.db"))
    from backend.core.config import get_settings

    get_settings.cache_clear()
    from backend.core.db import connect, migrate

    return connect()


def test_migrations_create_v1_tables(tmp_path, monkeypatch):
    conn = _fresh_conn(tmp_path, monkeypatch)
    from backend.core.db import migrate

    ran = migrate(conn)
    tables = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"users", "sessions", "turns", "costs", "settings"} <= tables
    assert ran == ["001_v1.sql"]


def test_migrations_are_idempotent(tmp_path, monkeypatch):
    conn = _fresh_conn(tmp_path, monkeypatch)
    from backend.core.db import migrate

    assert migrate(conn) == ["001_v1.sql"]
    assert migrate(conn) == []


def test_local_user_seeded(tmp_path, monkeypatch):
    conn = _fresh_conn(tmp_path, monkeypatch)
    from backend.core.db import migrate

    migrate(conn)
    row = conn.execute("SELECT id, name FROM users WHERE id = 1").fetchone()
    assert row is not None and row["name"] == "me"
