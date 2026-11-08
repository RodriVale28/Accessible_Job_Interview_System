
"""S2-4.1: Tests for accessibility settings - Sublime Mpanda."""

import uuid


def test_get_default_settings(client, user):
    """Users without saved settings receive the defaults."""
    response = client.get("/api/settings", headers=user)

    assert response.status_code == 200
    assert response.json() == {
        "text_size": "md",
        "theme": "light",
        "font": "default",
        "read_aloud": False,
    }


def test_save_and_retrieve_settings(client, user):
    """A user can save and retrieve accessibility settings."""
    settings = {
        "text_size": "lg",
        "theme": "dark",
        "font": "dyslexic",
        "read_aloud": True,
    }

    response = client.put(
        "/api/settings",
        headers=user,
        json=settings,
    )

    assert response.status_code == 200
    assert response.json() == settings

    retrieved = client.get("/api/settings", headers=user)

    assert retrieved.status_code == 200
    assert retrieved.json() == settings


def test_settings_are_isolated_by_user(client, user):
    """Another user cannot access saved settings."""
    settings = {
        "text_size": "xl",
        "theme": "contrast",
        "font": "default",
        "read_aloud": True,
    }

    client.put("/api/settings", headers=user, json=settings)

    another_user = {
        "X-User-Id": str(uuid.uuid4()),
    }

    response = client.get(
        "/api/settings",
        headers=another_user,
    )

    assert response.status_code == 200
    assert response.json() != settings
    assert response.json()["theme"] == "light"


def test_invalid_settings_rejected(client, user):
    """Invalid accessibility settings return HTTP 422."""
    response = client.put(
        "/api/settings",
        headers=user,
        json={
            "text_size": "gigantic",
            "theme": "dark",
            "font": "default",
            "read_aloud": False,
        },
    )

    assert response.status_code == 422


def test_extra_settings_fields_rejected(client, user):
    """Unknown fields are rejected by the request model."""
    response = client.put(
        "/api/settings",
        headers=user,
        json={
            "text_size": "md",
            "theme": "light",
            "font": "default",
            "read_aloud": False,
            "unknown_field": "value",
        },
    )

    assert response.status_code == 422



def test_settings_require_authentication(client, monkeypatch):
    """Both settings endpoints require an authenticated user."""
    from app import config

    monkeypatch.setattr(config, "ALLOW_GUEST", False)

    response_get = client.get("/api/settings")
    response_put = client.put(
        "/api/settings",
        json={
            "text_size": "md",
            "theme": "light",
            "font": "default",
            "read_aloud": False,
        },
    )

    assert response_get.status_code == 401
    assert response_put.status_code == 401
