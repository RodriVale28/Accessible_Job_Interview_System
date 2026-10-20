"""Smoke test: the API starts and answers /health."""


def test_health_endpoint_responds(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True
