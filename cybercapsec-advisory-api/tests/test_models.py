"""Tests for multi-tenant data isolation and model invariants."""
import pytest
from fastapi import HTTPException

from app.core.tenancy import get_tenant_object_or_404
from app.models import (
    Assessment,
    AssessmentStatus,
    Company,
    Sector,
    SubscriptionTier,
    User,
    UserRole,
)


def _make_company(db, name: str, slug: str) -> Company:
    company = Company(
        name=name,
        slug=slug,
        country="NG",
        sector=Sector.FINTECH,
        subscription_tier=SubscriptionTier.FREE,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def _make_user(db, company: Company, email: str) -> User:
    user = User(
        company_id=company.id,
        email=email,
        hashed_password="hash",
        full_name="Test User",
        role=UserRole.OWNER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestTenantIsolation:
    def test_get_tenant_object_returns_owned_object(self, db_session):
        company = _make_company(db_session, "Acme", "acme")
        user = _make_user(db_session, company, "u@acme.ng")

        assessment = Assessment(
            company_id=company.id,
            submitted_by_user_id=user.id,
            status=AssessmentStatus.DRAFT,
            responses={"sector": "fintech"},
        )
        db_session.add(assessment)
        db_session.commit()
        db_session.refresh(assessment)

        result = get_tenant_object_or_404(
            db_session, Assessment, assessment.id, company.id
        )
        assert result.id == assessment.id

    def test_get_tenant_object_raises_for_other_companies_data(self, db_session):
        co_a = _make_company(db_session, "Alpha", "alpha")
        co_b = _make_company(db_session, "Beta", "beta")
        user_a = _make_user(db_session, co_a, "a@alpha.ng")

        assessment = Assessment(
            company_id=co_a.id,
            submitted_by_user_id=user_a.id,
            status=AssessmentStatus.DRAFT,
            responses={},
        )
        db_session.add(assessment)
        db_session.commit()
        db_session.refresh(assessment)

        # Looking up co_a's assessment using co_b's id should 404
        with pytest.raises(HTTPException) as exc:
            get_tenant_object_or_404(
                db_session, Assessment, assessment.id, co_b.id
            )
        assert exc.value.status_code == 404

    def test_get_tenant_object_raises_for_unknown_id(self, db_session):
        company = _make_company(db_session, "Acme", "acme")
        with pytest.raises(HTTPException) as exc:
            get_tenant_object_or_404(
                db_session, Assessment, "no-such-id", company.id
            )
        assert exc.value.status_code == 404


class TestCompanyModel:
    def test_company_defaults(self, db_session):
        company = _make_company(db_session, "Default Co", "default-co")
        assert company.is_active is True
        assert company.subscription_tier == SubscriptionTier.FREE
        assert company.country == "NG"

    def test_user_belongs_to_company(self, db_session):
        company = _make_company(db_session, "Acme", "acme")
        user = _make_user(db_session, company, "u@acme.ng")
        assert user.company.id == company.id
        assert user in company.users
