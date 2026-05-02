"""Tests for the auth endpoints: signup, login, refresh, me."""
import pytest


class TestSignup:
    def test_signup_creates_user_and_company(self, client, signup_payload):
        resp = client.post("/api/v1/auth/signup", json=signup_payload)
        assert resp.status_code == 201, resp.text
        body = resp.json()

        assert body["user"]["email"] == signup_payload["email"]
        assert body["user"]["full_name"] == signup_payload["full_name"]
        assert body["user"]["role"] == "owner"

        assert body["company"]["name"] == signup_payload["company_name"]
        assert body["company"]["sector"] == "fintech"
        assert body["company"]["country"] == "NG"
        assert body["company"]["slug"] == "acme-fintech-ltd"
        assert body["company"]["subscription_tier"] == "free"

        assert "access_token" in body["tokens"]
        assert "refresh_token" in body["tokens"]
        assert body["tokens"]["token_type"] == "bearer"

    def test_signup_duplicate_email_rejected(self, client, signup_payload):
        first = client.post("/api/v1/auth/signup", json=signup_payload)
        assert first.status_code == 201

        second = client.post("/api/v1/auth/signup", json=signup_payload)
        assert second.status_code == 409

    def test_signup_assigns_unique_slugs(self, client, signup_payload):
        # Two companies with the same name should get distinct slugs
        first_payload = {**signup_payload}
        client.post("/api/v1/auth/signup", json=first_payload)

        second_payload = {**signup_payload, "email": "second@acmefintech.ng"}
        resp = client.post("/api/v1/auth/signup", json=second_payload)
        assert resp.status_code == 201
        assert resp.json()["company"]["slug"] == "acme-fintech-ltd-2"

    def test_signup_rejects_short_password(self, client, signup_payload):
        signup_payload["password"] = "short"
        resp = client.post("/api/v1/auth/signup", json=signup_payload)
        assert resp.status_code == 422

    def test_signup_rejects_invalid_email(self, client, signup_payload):
        signup_payload["email"] = "not-an-email"
        resp = client.post("/api/v1/auth/signup", json=signup_payload)
        assert resp.status_code == 422

    def test_signup_normalizes_email_lowercase(self, client, signup_payload):
        signup_payload["email"] = "FOUNDER@ACMEFINTECH.NG"
        resp = client.post("/api/v1/auth/signup", json=signup_payload)
        assert resp.status_code == 201
        assert resp.json()["user"]["email"] == "founder@acmefintech.ng"


class TestLogin:
    def test_login_with_correct_credentials(self, client, signup_payload):
        client.post("/api/v1/auth/signup", json=signup_payload)
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": signup_payload["email"], "password": signup_payload["password"]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body

    def test_login_with_wrong_password(self, client, signup_payload):
        client.post("/api/v1/auth/signup", json=signup_payload)
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": signup_payload["email"], "password": "WrongPassword123!"},
        )
        assert resp.status_code == 401

    def test_login_with_unknown_user(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@nowhere.ng", "password": "DoesntMatter1!"},
        )
        assert resp.status_code == 401

    def test_login_is_case_insensitive_for_email(self, client, signup_payload):
        client.post("/api/v1/auth/signup", json=signup_payload)
        resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": signup_payload["email"].upper(),
                "password": signup_payload["password"],
            },
        )
        assert resp.status_code == 200


class TestRefresh:
    def test_refresh_issues_new_tokens(self, client, signup_payload):
        signup = client.post("/api/v1/auth/signup", json=signup_payload).json()
        refresh_token = signup["tokens"]["refresh_token"]

        resp = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert resp.status_code == 200
        new_tokens = resp.json()
        assert new_tokens["access_token"]
        assert new_tokens["refresh_token"]

    def test_refresh_rejects_access_token(self, client, signup_payload):
        signup = client.post("/api/v1/auth/signup", json=signup_payload).json()
        access_token = signup["tokens"]["access_token"]

        resp = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": access_token}
        )
        assert resp.status_code == 401

    def test_refresh_rejects_garbage(self, client):
        resp = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "not.a.valid.jwt"}
        )
        assert resp.status_code == 401


class TestMe:
    def test_me_returns_current_user(self, authed_client, signup_payload):
        resp = authed_client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == signup_payload["email"]
        assert body["role"] == "owner"

    def test_me_requires_auth(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_me_rejects_garbage_token(self, client):
        resp = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"}
        )
        assert resp.status_code == 401
