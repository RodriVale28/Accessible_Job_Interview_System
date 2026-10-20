"""S1-0.1 Login: Supabase tokens are checked, guests only when allowed, past interviews list."""
import time
import uuid
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from app import config
from app.api import deps

PROJECT = "https://example-ref.supabase.co"
KEY = ec.generate_private_key(ec.SECP256R1())
SETUP = {"job_title": "Backend Developer", "difficulty": "Easy", "duration_min": 15}


@pytest.fixture(autouse=True)
def login_on(monkeypatch):
    """Login configured, guest ids off, public key served from a stub instead of Supabase."""
    monkeypatch.setattr(config, "SUPABASE_URL", PROJECT)
    monkeypatch.setattr(config, "ALLOW_GUEST", False)
    stub = SimpleNamespace(get_signing_key_from_jwt=lambda _t: SimpleNamespace(key=KEY.public_key()))
    monkeypatch.setattr(deps, "_jwks", stub)


def token(sub=None, key=KEY, **overrides):
    claims = {"sub": sub or str(uuid.uuid4()), "aud": "authenticated", "iss": f"{PROJECT}/auth/v1",
              "exp": int(time.time()) + 3600, **overrides}
    return {"Authorization": "Bearer " + jwt.encode(claims, key, algorithm="ES256")}


def test_valid_token_starts_and_lists_own_sessions(client):
    me, other = token(), token()
    assert client.post("/api/sessions", headers=me, json=SETUP).status_code == 201
    assert client.post("/api/sessions", headers=other, json=SETUP).status_code == 201
    mine = client.get("/api/sessions", headers=me)
    assert mine.status_code == 200
    assert [s["job_title"] for s in mine.json()] == ["Backend Developer"]
    assert mine.json()[0]["status"] == "in_progress"


def test_same_user_sees_session_after_new_login(client):
    sub = str(uuid.uuid4())
    sid = client.post("/api/sessions", headers=token(sub), json=SETUP).json()["session_id"]
    # a fresh token for the same account (log out, log back in)
    again = token(sub, iat=int(time.time()) - 5)
    assert client.get(f"/api/sessions/{sid}", headers=again).status_code == 200
    assert [s["session_id"] for s in client.get("/api/sessions", headers=again).json()] == [sid]


@pytest.mark.parametrize("bad", [
    {"exp": int(time.time()) - 10},                    # expired
    {"aud": "anon"},                                   # not a signed-in user
    {"iss": "https://someone-else.supabase.co/auth/v1"},
])
def test_rejects_bad_tokens(client, bad):
    r = client.post("/api/sessions", headers=token(**bad), json=SETUP)
    assert r.status_code == 401


def test_rejects_token_signed_by_another_key(client):
    r = client.get("/api/sessions", headers=token(key=ec.generate_private_key(ec.SECP256R1())))
    assert r.status_code == 401


def test_guest_id_ignored_when_login_required(client):
    r = client.get("/api/sessions", headers={"X-User-Id": str(uuid.uuid4())})
    assert r.status_code == 401
    assert "log in" in r.json()["detail"]


def test_guest_id_works_when_allowed(client, monkeypatch):
    monkeypatch.setattr(config, "ALLOW_GUEST", True)
    guest = {"X-User-Id": str(uuid.uuid4())}
    assert client.post("/api/sessions", headers=guest, json=SETUP).status_code == 201
    assert len(client.get("/api/sessions", headers=guest).json()) == 1
