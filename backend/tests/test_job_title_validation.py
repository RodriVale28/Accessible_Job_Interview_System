"""TC-002: job titles made only of numbers or special characters are rejected - owner: Christofer Arias"""
import pytest


def _post(client, user, job_title):
    return client.post("/api/sessions", headers=user,
                       json={"job_title": job_title, "difficulty": "Easy", "duration_min": 15})


@pytest.mark.parametrize("job_title", ["12345", "!!!@@", "123!!", "  42  ", "#1 - $"])
def test_rejects_job_title_without_letters(client, user, job_title):
    r = _post(client, user, job_title)
    assert r.status_code == 422, r.text
    assert "must include letters" in r.text


@pytest.mark.parametrize("job_title", ["Junior Software Engineer", "C++ Developer",
                                       "Software Engineer II", "Tier 2 Support", "QA"])
def test_accepts_job_title_with_letters(client, user, job_title):
    r = _post(client, user, job_title)
    assert r.status_code == 201, r.text
    assert r.json()["job_title"] == job_title
