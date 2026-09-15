from fastapi.testclient import TestClient


def test_health(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DB_PATH", str(tmp_path / "test.db"))
    from backend.core.config import get_settings

    get_settings.cache_clear()
    from backend.main import app

    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["ok"] is True
