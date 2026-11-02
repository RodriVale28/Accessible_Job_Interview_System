"""S2-1.3 Tests for job title to role matching and the roles endpoints."""
import pytest

from app.services.role_matcher import match_role
from tests.conftest import FAKE_ROLES as ROLES


@pytest.fixture(autouse=True)
def ai_off(monkeypatch):
    """Default: the AI is unavailable, so the keyword fallback is used."""
    monkeypatch.setattr("app.services.role_matcher._ask_json", lambda s, u: None)


@pytest.mark.parametrize("title,expected", [
    ("Junior Data Analyst", "Data Analyst"),
    ("Help desk technician", "IT Support"),
    ("Call center agent", "Customer Service"),
    ("Pastry chef", None),
])
def test_keyword_matching(title, expected):
    result = match_role(title, ROLES)
    assert result["role_name"] == expected
    assert result["matched_by"] == "keyword"
    assert (result["role_id"] is None) == (expected is None)


def test_keywords_match_whole_words_only():
    # "it" must not match inside "pastry"/"waiter"
    assert match_role("Waiter", ROLES)["role_id"] is None


def test_tie_means_no_match():
    roles = [
        {"id": 1, "name": "A", "keywords": ["alpha"]},
        {"id": 2, "name": "B", "keywords": ["beta"]},
    ]
    assert match_role("alpha beta", roles)["role_id"] is None


def test_no_roles_means_no_match():
    assert match_role("Data Analyst", [])["role_id"] is None


def test_ai_pick_is_used(monkeypatch):
    monkeypatch.setattr("app.services.role_matcher._ask_json", lambda s, u: {"role": "IT Support"})
    assert match_role("Pastry chef", ROLES) == {"role_id": 3, "role_name": "IT Support", "matched_by": "ai"}


def test_ai_none_means_no_match(monkeypatch):
    monkeypatch.setattr("app.services.role_matcher._ask_json", lambda s, u: {"role": "none"})
    assert match_role("Junior Data Analyst", ROLES) == {"role_id": None, "role_name": None, "matched_by": "ai"}


@pytest.mark.parametrize("reply", [{"role": "Astronaut"}, {"oops": 1}, {"role": 5}, None])
def test_bad_ai_reply_falls_back_to_keywords(monkeypatch, reply):
    monkeypatch.setattr("app.services.role_matcher._ask_json", lambda s, u: reply)
    result = match_role("Junior Data Analyst", ROLES)
    assert result["role_name"] == "Data Analyst"
    assert result["matched_by"] == "keyword"


def test_only_the_job_title_goes_to_the_ai(monkeypatch):
    seen = {}

    def fake(system, user):
        seen["user"] = user
        return None

    monkeypatch.setattr("app.services.role_matcher._ask_json", fake)
    match_role("Junior Data Analyst", ROLES)
    assert "Junior Data Analyst" in seen["user"]


def test_get_roles(client, user, fake_roles):
    r = client.get("/api/roles", headers=user)
    assert r.status_code == 200
    assert r.json() == [{"id": x["id"], "name": x["name"]} for x in ROLES]


def test_match_endpoint(client, user, fake_roles):
    r = client.post("/api/roles/match", json={"job_title": "Junior Data Analyst"}, headers=user)
    assert r.status_code == 200
    assert r.json() == {"role_id": 2, "role_name": "Data Analyst", "matched_by": "keyword"}


def test_match_endpoint_no_match(client, user, fake_roles):
    r = client.post("/api/roles/match", json={"job_title": "Pastry chef"}, headers=user)
    assert r.status_code == 200
    assert r.json() == {"role_id": None, "role_name": None, "matched_by": "keyword"}


@pytest.mark.parametrize("payload", [{"job_title": ""}, {"job_title": "   "}, {}, {"job_title": "x", "extra": 1}])
def test_match_bad_input_422(client, user, fake_roles, payload):
    assert client.post("/api/roles/match", json=payload, headers=user).status_code == 422


def test_logged_out_401(client, fake_roles):
    assert client.get("/api/roles").status_code == 401
    assert client.post("/api/roles/match", json={"job_title": "x"}).status_code == 401
