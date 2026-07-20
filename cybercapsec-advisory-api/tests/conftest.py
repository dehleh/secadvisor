"""Test fixtures.

Tests use an in-memory SQLite DB so the suite runs without external services.
Postgres-specific features (like JSONB) are avoided in models in favor of the
generic JSON type, so SQLite is a faithful test surrogate.
"""
import os

# Set test env vars before importing the app
os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-chars-long-please-aaaa")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.environ.setdefault("USE_MOCK_AI", "true")

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture(scope="function")
def test_engine():
    """A fresh in-memory SQLite engine per test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """A DB session bound to the test engine."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """A TestClient with the DB dependency overridden to use the test session."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def signup_payload() -> dict:
    """A canonical signup request payload."""
    return {
        "email": "founder@acmefintech.ng",
        "password": "Str0ngPassword!",
        "full_name": "Ada Okonkwo",
        "job_title": "Founder & CEO",
        "company_name": "Acme Fintech Ltd",
        "country": "NG",
        "sector": "fintech",
        "size": "small",
        "stage": "seed",
    }


@pytest.fixture
def authed_client(client, signup_payload, db_session):
    """A TestClient that has signed up and is authenticated.

    The created company is upgraded to GROWTH tier so ordinary feature tests
    can enter the licensed workspace. Tests that specifically exercise the
    no-licence state use the ``free_tier_client`` fixture below.
    """
    resp = client.post("/api/v1/auth/signup", json=signup_payload)
    assert resp.status_code == 201, resp.text
    tokens = resp.json()["tokens"]
    client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})

    # Upgrade to unlimited tier so limit checks don't bite ordinary tests
    from app.models import Company, SubscriptionTier

    company_id = resp.json()["company"]["id"]
    company = db_session.query(Company).filter(Company.id == company_id).first()
    if company is not None:
        company.subscription_tier = SubscriptionTier.GROWTH
        db_session.commit()

    return client


@pytest.fixture
def free_tier_client(client, signup_payload):
    """A TestClient where the company stays on the FREE tier (default).

    Use this fixture in tests that specifically exercise the no-licence gate.
    """
    resp = client.post("/api/v1/auth/signup", json=signup_payload)
    assert resp.status_code == 201, resp.text
    tokens = resp.json()["tokens"]
    client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
    return client


@pytest.fixture
def license_company(db_session):
    """Upgrade a manually-created test company so workspace setup can proceed."""

    def _license(company_id: str):
        from app.models import Company, SubscriptionTier

        company = db_session.query(Company).filter(Company.id == company_id).first()
        assert company is not None
        company.subscription_tier = SubscriptionTier.GROWTH
        db_session.commit()

    return _license
