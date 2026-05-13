"""Tests for the internal /admin marketing-data API."""
import os

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import get_db
from app.main import app


ADMIN_KEY = "test-admin-key-do-not-use-in-prod"


@pytest.fixture
def admin_client(db_session, monkeypatch):
    """A TestClient with ADMIN_API_KEY set in settings."""
    # Settings is cached via lru_cache; mutate the live instance.
    settings = get_settings()
    monkeypatch.setattr(settings, "ADMIN_API_KEY", ADMIN_KEY)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_admin_client(admin_client, signup_payload):
    """Admin client with one company already signed up."""
    resp = admin_client.post("/api/v1/auth/signup", json=signup_payload)
    assert resp.status_code == 201, resp.text
    return admin_client


def _h(extra: dict | None = None) -> dict:
    h = {"X-Admin-Key": ADMIN_KEY}
    if extra:
        h.update(extra)
    return h


class TestAdminAuth:
    def test_missing_key_returns_401(self, seeded_admin_client):
        resp = seeded_admin_client.get("/api/v1/admin/companies")
        assert resp.status_code == 401

    def test_wrong_key_returns_401(self, seeded_admin_client):
        resp = seeded_admin_client.get(
            "/api/v1/admin/companies", headers={"X-Admin-Key": "nope"}
        )
        assert resp.status_code == 401

    def test_disabled_when_key_unset(self, db_session, monkeypatch):
        settings = get_settings()
        monkeypatch.setattr(settings, "ADMIN_API_KEY", "")

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as c:
            resp = c.get(
                "/api/v1/admin/companies", headers={"X-Admin-Key": "anything"}
            )
        app.dependency_overrides.clear()
        assert resp.status_code == 503


class TestAdminCompanies:
    def test_list_returns_signed_up_company(self, seeded_admin_client, signup_payload):
        resp = seeded_admin_client.get("/api/v1/admin/companies", headers=_h())
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total"] == 1
        item = body["items"][0]
        assert item["name"] == signup_payload["company_name"]
        assert item["country"] == signup_payload["country"]
        assert item["sector"] == signup_payload["sector"]
        assert item["owner_email"] == signup_payload["email"]
        assert item["owner_name"] == signup_payload["full_name"]
        assert item["user_count"] == 1
        assert item["assessment_count"] == 0
        assert item["completed_assessment_count"] == 0

    def test_filter_by_country(self, seeded_admin_client):
        resp = seeded_admin_client.get(
            "/api/v1/admin/companies?country=KE", headers=_h()
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

        resp = seeded_admin_client.get(
            "/api/v1/admin/companies?country=NG", headers=_h()
        )
        assert resp.json()["total"] == 1

    def test_filter_by_sector(self, seeded_admin_client):
        resp = seeded_admin_client.get(
            "/api/v1/admin/companies?sector=fintech", headers=_h()
        )
        assert resp.json()["total"] == 1
        resp = seeded_admin_client.get(
            "/api/v1/admin/companies?sector=healthtech", headers=_h()
        )
        assert resp.json()["total"] == 0

    def test_search_by_name(self, seeded_admin_client):
        resp = seeded_admin_client.get(
            "/api/v1/admin/companies?q=acme", headers=_h()
        )
        assert resp.json()["total"] == 1
        resp = seeded_admin_client.get(
            "/api/v1/admin/companies?q=zzznotfound", headers=_h()
        )
        assert resp.json()["total"] == 0

    def test_csv_export(self, seeded_admin_client, signup_payload):
        resp = seeded_admin_client.get("/api/v1/admin/companies.csv", headers=_h())
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        body = resp.text
        assert "company_name,website,country" in body
        assert signup_payload["company_name"] in body
        assert signup_payload["email"] in body


class TestAdminStats:
    def test_stats_zero_when_empty(self, admin_client):
        resp = admin_client.get("/api/v1/admin/stats", headers=_h())
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_companies"] == 0
        assert body["total_users"] == 0

    def test_stats_after_signup(self, seeded_admin_client):
        resp = seeded_admin_client.get("/api/v1/admin/stats", headers=_h())
        body = resp.json()
        assert body["total_companies"] == 1
        assert body["active_companies"] == 1
        assert body["total_users"] == 1
        assert body["by_country"] == {"NG": 1}
        assert body["by_sector"] == {"fintech": 1}
        assert body["by_tier"] == {"free": 1}
