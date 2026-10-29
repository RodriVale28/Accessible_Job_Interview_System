"""Access control: a user can never read or change another user's data (IDOR / BOLA).

Alice is the victim, Mallory the attacker. Both are signed in with real Supabase-style
tokens (guest ids off), the way the deployed site runs. For every object Alice owns,
Mallory gets exactly what she would get for an id that does not exist (404, same
message), sees none of Alice's data, and changes nothing.

Covered now: interview sessions, answers, results and the past-interviews list (history).
Written ahead of Sprint 2 and skipped until their routes exist:
    practice   POST /api/practice {question_id, text} -> {id, ...}
               GET  /api/practice (own attempts), GET /api/practice/{id}
    settings   GET  /api/settings, PUT /api/settings {text_size, theme, font, read_aloud}

test_every_routed_object_has_an_access_test fails when a new /api route takes an id
that no test here covers, so new endpoints cannot skip this check.
"""
import copy
import json
import re
import time
import uuid
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from app import config
from app.api import deps
from app.main import app

PROJECT = "https://example-ref.supabase.co"
KEY = ec.generate_private_key(ec.SECP256R1())
ALICE_ID, MALLORY_ID = str(uuid.uuid4()), str(uuid.uuid4())
ALICE_TITLE = "Alice Secret Role"
ALICE_ANSWER = "ALICE-PRIVATE-ANSWER a stack is LIFO with push and pop"
MISSING_ID = 987654

# Objects reachable by id, and the fixture that creates one for Alice.
OWNED_PREFIXES = {"/api/sessions/{id}": "alice_session", "/api/practice/{id}": "alice_practice"}


def claims(sub, **overrides):
    return {"sub": sub, "aud": "authenticated", "iss": f"{PROJECT}/auth/v1",
            "exp": int(time.time()) + 3600, **overrides}


def bearer(sub, key=KEY, algorithm="ES256", **overrides):
    return {"Authorization": "Bearer " + jwt.encode(claims(sub, **overrides), key, algorithm=algorithm)}


ALICE, MALLORY = bearer(ALICE_ID), bearer(MALLORY_ID)


@pytest.fixture(autouse=True)
def login_on(monkeypatch):
    """Login required, guest ids off, signing key served from a stub instead of Supabase."""
    monkeypatch.setattr(config, "SUPABASE_URL", PROJECT)
    monkeypatch.setattr(config, "ALLOW_GUEST", False)
    stub = SimpleNamespace(get_signing_key_from_jwt=lambda _t: SimpleNamespace(key=KEY.public_key()))
    monkeypatch.setattr(deps, "_jwks", stub)


def api_routes():
    """(method, path template) for every /api route, read from the OpenAPI schema."""
    return sorted((m.upper(), path) for path, ops in app.openapi()["paths"].items()
                  if path.startswith("/api") for m in ops)


def has_route(path):
    return any(p == path for _, p in api_routes())


def normalise(path):
    return re.sub(r"\{[^}]+\}", "{id}", path)


def routes_under(prefix):
    """(method, path template) for every route on an object of this kind."""
    return [(m, p) for m, p in api_routes() if normalise(p).startswith(prefix)]


def fill(path, object_id):
    return re.sub(r"\{[^}]+\}", str(object_id), path, count=1)


def call(client, method, path, headers, body=None):
    if method in {"POST", "PUT", "PATCH"}:
        return client.request(method, path, headers=headers, json=body or {})
    return client.request(method, path, headers=headers)


def start(client, headers, job_title="Backend Developer"):
    r = client.post("/api/sessions", headers=headers,
                    json={"job_title": job_title, "difficulty": "Easy", "duration_min": 15})
    assert r.status_code == 201, r.text
    return r.json()


def snapshot(repo):
    return copy.deepcopy((repo.sessions, repo.session_questions, repo.responses, repo.feedback))


def assert_no_alice_data(r):
    assert ALICE_TITLE not in r.text
    assert "ALICE-PRIVATE" not in r.text
    assert ALICE_ID not in r.text


def assert_same_as_missing(client, method, path, attempt, body=None):
    """Alice's object must look exactly like one that does not exist."""
    missing = call(client, method, fill(path, MISSING_ID), MALLORY, body)
    assert attempt.status_code in (404, 405), attempt.text
    assert (attempt.status_code, attempt.json()) == (missing.status_code, missing.json())


# --- fixtures: Alice's data ---------------------------------------------------------

@pytest.fixture(params=["in_progress", "answered", "completed"])
def alice_session(request, client):
    """One of Alice's sessions, in each state an attacker could find it in."""
    s = start(client, ALICE, ALICE_TITLE)
    sid = s["session_id"]
    if request.param in ("answered", "completed"):
        r = client.post(f"/api/sessions/{sid}/answers", headers=ALICE,
                        json={"question_id": s["question"]["id"], "text": ALICE_ANSWER})
        assert r.status_code == 200, r.text
    current = client.get(f"/api/sessions/{sid}", headers=ALICE).json()
    if request.param == "completed":
        assert client.post(f"/api/sessions/{sid}/complete", headers=ALICE).status_code == 200
    question = current["question"] or s["question"]
    # Worst case: Mallory knows the id and the current question.
    return SimpleNamespace(id=sid, body={"question_id": question["id"], "text": "MALLORY WAS HERE"})


@pytest.fixture
def alice_practice(client, repo):
    if not has_route("/api/practice"):
        pytest.skip("Practice mode not implemented yet")
    r = client.post("/api/practice", headers=ALICE,
                    json={"question_id": next(iter(repo.questions)), "text": ALICE_ANSWER})
    assert r.status_code in (200, 201), r.text
    return SimpleNamespace(id=r.json()["id"], body={"text": "MALLORY WAS HERE"})


# --- every route ---------------------------------------------------------------------

@pytest.mark.parametrize("method,path", api_routes())
def test_every_api_route_requires_login(client, method, path):
    r = call(client, method, fill(path, 1), {})
    assert r.status_code == 401, f"{method} {path} answered {r.status_code} without a login"


def test_every_routed_object_has_an_access_test():
    for _, path in api_routes():
        if "{" in path:
            assert any(normalise(path).startswith(p) for p in OWNED_PREFIXES), (
                f"{path} takes an id but has no IDOR test: add its object to OWNED_PREFIXES"
            )


# --- interview sessions, answers and results ------------------------------------------

@pytest.mark.parametrize("method,path", routes_under("/api/sessions/{id}"))
def test_cannot_read_or_change_another_users_session(client, repo, alice_session, method, path):
    before = snapshot(repo)

    r = call(client, method, fill(path, alice_session.id), MALLORY, alice_session.body)

    assert_same_as_missing(client, method, path, r, alice_session.body)
    assert_no_alice_data(r)
    assert snapshot(repo) == before


def test_owner_still_has_access_after_attack(client, alice_session):
    for m, p in routes_under("/api/sessions/{id}"):
        call(client, m, fill(p, alice_session.id), MALLORY, alice_session.body)

    r = client.get(f"/api/sessions/{alice_session.id}", headers=ALICE)
    assert r.status_code == 200
    assert r.json()["job_title"] == ALICE_TITLE


@pytest.mark.parametrize("variant", ["0{id}", "00{id}", "{id}%20", "-{id}", "{id}.0",
                                     "{id}abc", "9223372036854775808", "1e1"])
def test_odd_ids_never_reach_another_users_session(client, alice_session, variant):
    path = "/api/sessions/" + variant.format(id=alice_session.id)
    for suffix in ("", "/results"):
        r = client.get(path + suffix, headers=MALLORY)
        assert r.status_code in (404, 422), r.text
        assert_no_alice_data(r)


def test_scanning_ids_finds_only_your_own_sessions(client):
    alice_ids = [start(client, ALICE, ALICE_TITLE)["session_id"] for _ in range(3)]
    mine = start(client, MALLORY)["session_id"]

    found = [sid for sid in range(0, max(alice_ids) + 5)
             if client.get(f"/api/sessions/{sid}", headers=MALLORY).status_code == 200]

    assert found == [mine]


def test_own_results_contain_nobody_elses_answers(client, alice_session):
    s = start(client, MALLORY)
    client.post(f"/api/sessions/{s['session_id']}/answers", headers=MALLORY,
                json={"question_id": s["question"]["id"], "text": "my answer"})

    r = client.post(f"/api/sessions/{s['session_id']}/complete", headers=MALLORY)

    assert r.status_code == 200
    assert_no_alice_data(r)


# --- past interviews (history) ---------------------------------------------------------

def test_history_lists_only_your_own_interviews(client):
    alice_ids = {start(client, ALICE, ALICE_TITLE)["session_id"] for _ in range(2)}
    mallory_ids = {start(client, MALLORY)["session_id"]}

    alice_list = client.get("/api/sessions", headers=ALICE)
    mallory_list = client.get("/api/sessions", headers=MALLORY)

    assert {s["session_id"] for s in alice_list.json()} == alice_ids
    assert {s["session_id"] for s in mallory_list.json()} == mallory_ids
    assert_no_alice_data(mallory_list)


@pytest.mark.parametrize("query", ["user_id={alice}", "uid={alice}", "user={alice}", "owner={alice}"])
def test_history_ignores_a_user_id_in_the_query(client, query):
    start(client, ALICE, ALICE_TITLE)
    mine = start(client, MALLORY)["session_id"]

    r = client.get("/api/sessions?" + query.format(alice=ALICE_ID), headers=MALLORY)

    assert r.status_code == 200
    assert [s["session_id"] for s in r.json()] == [mine]


def test_cannot_create_a_session_owned_by_someone_else(client):
    r = client.post("/api/sessions", headers=MALLORY, json={
        "job_title": "Planted", "difficulty": "Easy", "duration_min": 15, "user_id": ALICE_ID,
    })

    assert r.status_code in (201, 422)
    assert client.get("/api/sessions", headers=ALICE).json() == []


# --- identity: only a valid token decides who you are ---------------------------------

@pytest.mark.parametrize("allow_guest", [False, True])
def test_guest_header_cannot_override_the_logged_in_user(client, monkeypatch, alice_session, allow_guest):
    monkeypatch.setattr(config, "ALLOW_GUEST", allow_guest)

    r = client.get(f"/api/sessions/{alice_session.id}", headers={**MALLORY, "X-User-Id": ALICE_ID})

    assert r.status_code == 404
    assert_no_alice_data(r)


def test_guest_header_with_a_real_users_id_is_refused_when_login_is_required(client, alice_session):
    r = client.get(f"/api/sessions/{alice_session.id}", headers={"X-User-Id": ALICE_ID})
    assert r.status_code == 401


@pytest.mark.parametrize("forged", [
    lambda: bearer(ALICE_ID, key=ec.generate_private_key(ec.SECP256R1())),     # attacker's own key
    lambda: {"Authorization": "Bearer " + jwt.encode(claims(ALICE_ID), None, algorithm="none")},
    lambda: {"Authorization": "Bearer " + jwt.encode(claims(ALICE_ID), "secret", algorithm="HS256")},
    lambda: bearer(ALICE_ID, exp=int(time.time()) - 120),                       # expired
    lambda: bearer(ALICE_ID, aud="anon"),                                       # not signed in
    lambda: bearer(ALICE_ID, iss="https://attacker.supabase.co/auth/v1"),       # other project
    lambda: {"Authorization": "Bearer " + _swap_sub(MALLORY, ALICE_ID)},        # payload edited
], ids=["other-key", "alg-none", "hs256", "expired", "anon", "other-issuer", "edited-payload"])
def test_forged_token_for_another_user_is_refused(client, alice_session, forged):
    r = client.get(f"/api/sessions/{alice_session.id}", headers=forged())

    assert r.status_code == 401
    assert_no_alice_data(r)


def _swap_sub(headers, sub):
    """Mallory's real token with the user id in its payload changed to Alice's."""
    head, _payload, sig = headers["Authorization"][7:].split(".")
    payload = jwt.utils.base64url_encode(json.dumps(claims(sub)).encode()).decode()
    return f"{head}.{payload}.{sig}"


# --- practice (Sprint 2) ----------------------------------------------------------------

@pytest.mark.parametrize("method,path", routes_under("/api/practice/{id}") or [("GET", "/api/practice/{id}")])
def test_cannot_read_or_change_another_users_practice(client, alice_practice, method, path):
    r = call(client, method, fill(path, alice_practice.id), MALLORY, alice_practice.body)

    assert_same_as_missing(client, method, path, r, alice_practice.body)
    assert_no_alice_data(r)
    still = client.get(f"/api/practice/{alice_practice.id}", headers=ALICE)
    assert still.status_code == 200
    assert ALICE_ANSWER in still.text


def test_practice_list_shows_only_your_own_attempts(client, alice_practice):
    r = client.get("/api/practice", headers=MALLORY)

    assert r.status_code == 200
    assert alice_practice.id not in [a["id"] for a in r.json()]
    assert_no_alice_data(r)


def test_practice_list_ignores_a_user_id_in_the_query(client, alice_practice):
    r = client.get(f"/api/practice?user_id={ALICE_ID}", headers=MALLORY)

    assert r.status_code == 200
    assert_no_alice_data(r)


# --- account settings (Sprint 2) --------------------------------------------------------

ALICE_SETTINGS = {"text_size": "xl", "theme": "dark", "font": "dyslexic", "read_aloud": True}
MALLORY_SETTINGS = {"text_size": "sm", "theme": "contrast", "font": "default", "read_aloud": False}


@pytest.fixture
def alice_settings(client):
    if not has_route("/api/settings"):
        pytest.skip("Account settings not implemented yet")
    r = client.put("/api/settings", headers=ALICE, json=ALICE_SETTINGS)
    assert r.status_code == 200, r.text


def alices_settings_unchanged(client):
    r = client.get("/api/settings", headers=ALICE)
    return r.status_code == 200 and {k: r.json().get(k) for k in ALICE_SETTINGS} == ALICE_SETTINGS


def test_cannot_read_another_users_settings(client, alice_settings):
    r = client.get("/api/settings", headers=MALLORY)

    assert r.status_code == 200
    assert {k: r.json().get(k) for k in ALICE_SETTINGS} != ALICE_SETTINGS
    assert ALICE_ID not in r.text


@pytest.mark.parametrize("query", ["user_id={alice}", "uid={alice}"])
def test_settings_ignore_a_user_id_in_the_query(client, alice_settings, query):
    r = client.get("/api/settings?" + query.format(alice=ALICE_ID), headers=MALLORY)

    assert r.status_code == 200
    assert {k: r.json().get(k) for k in ALICE_SETTINGS} != ALICE_SETTINGS


@pytest.mark.parametrize("extra", [{"user_id": ALICE_ID}, {"uid": ALICE_ID}])
def test_cannot_change_another_users_settings_through_the_body(client, alice_settings, extra):
    client.put("/api/settings", headers=MALLORY, json={**MALLORY_SETTINGS, **extra})

    assert alices_settings_unchanged(client)


def test_cannot_change_another_users_settings_through_the_path(client, alice_settings):
    for method in ("GET", "PUT", "PATCH", "DELETE"):
        r = call(client, method, f"/api/settings/{ALICE_ID}", MALLORY, MALLORY_SETTINGS)
        assert r.status_code in (404, 405), f"{method} /api/settings/<alice> answered {r.status_code}"
        assert_no_alice_data(r)

    assert alices_settings_unchanged(client)


def test_changing_your_settings_leaves_others_alone(client, alice_settings):
    assert client.put("/api/settings", headers=MALLORY, json=MALLORY_SETTINGS).status_code == 200

    assert alices_settings_unchanged(client)
