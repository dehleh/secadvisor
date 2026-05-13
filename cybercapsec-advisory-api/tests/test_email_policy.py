"""Tests for the company-email-only policy on signup, login, and invite."""
import pytest


FREE_EMAIL_PAYLOAD_BASE = {
    "password": "Str0ngPass!",
    "full_name": "Free Email User",
    "company_name": "Free Co",
    "country": "NG",
    "sector": "fintech",
    "size": "small",
    "stage": "seed",
}


@pytest.mark.parametrize(
    "email",
    [
        "founder@gmail.com",
        "ceo@yahoo.com",
        "owner@hotmail.com",
        "me@outlook.com",
        "test@icloud.com",
        "x@protonmail.com",
        "x@aol.com",
        "x@mailinator.com",
    ],
)
def test_signup_rejects_free_email_domains(client, email):
    payload = {**FREE_EMAIL_PAYLOAD_BASE, "email": email}
    resp = client.post("/api/v1/auth/signup", json=payload)
    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert any(
        "company email" in err.get("msg", "").lower()
        for err in body["detail"]
    ), body


def test_signup_accepts_company_email(client):
    payload = {**FREE_EMAIL_PAYLOAD_BASE, "email": "founder@acmefintech.ng"}
    resp = client.post("/api/v1/auth/signup", json=payload)
    assert resp.status_code == 201, resp.text


def test_login_rejects_free_email_domain(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "anyone@gmail.com", "password": "whatever123"},
    )
    assert resp.status_code == 422, resp.text


def test_invite_rejects_free_email_domain(authed_client):
    resp = authed_client.post(
        "/api/v1/users",
        json={
            "email": "newhire@gmail.com",
            "full_name": "Free Email Newhire",
            "role": "member",
        },
    )
    assert resp.status_code == 422, resp.text
