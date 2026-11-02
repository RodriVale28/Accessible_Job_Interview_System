"""Smoke tests for API and database health endpoints."""


def test_health_endpoint_responds(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True

def test_db_health_endpoint_success(client, monkeypatch):
    class HealthyRepo:
        def ping(self):
            return True

    monkeypatch.setattr("app.main.get_repo", lambda: HealthyRepo())

    r = client.get("/health/db")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_db_health_endpoint_database_down(client, monkeypatch):
    class UnhealthyRepo:
        def ping(self):
            return False

    monkeypatch.setattr("app.main.get_repo", lambda: UnhealthyRepo())

    r = client.get("/health/db")
    assert r.status_code == 503