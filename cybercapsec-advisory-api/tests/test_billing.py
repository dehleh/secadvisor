"""Session 7 tests — Paystack-backed billing.

Covers:
  - Pricing catalog (currency-aware)
  - Paid licence enforcement for workspace access
  - Webhook signature verification
  - Mock Paystack client behaves like the real one
  - End-to-end checkout flow with mock client
  - Webhook event processing (subscription.create, subscription.disable, etc.)
"""
import json

import pytest

from app.api import billing as billing_api
from app.main import app
from app.models import (
    BillingCurrency,
    Company,
    Subscription,
    SubscriptionStatus,
    SubscriptionTier,
)
from app.services.billing import (
    CATALOG,
    MockPaystackClient,
    PaystackError,
    compute_paystack_signature,
    get_plan,
    plans_for_currency,
    verify_paystack_signature,
)
from app.services.billing.limits import TIER_LIMITS


# Module-level fixture: route the billing client dependency to a mock for all
# tests in this file. The mock instance is shared across requests within a test
# (so a checkout in one request can be matched to a webhook in the next).


@pytest.fixture
def mock_paystack(monkeypatch):
    """Inject a fresh MockPaystackClient via FastAPI's dependency overrides."""
    client = MockPaystackClient()
    app.dependency_overrides[billing_api.get_billing_client] = lambda: client
    # Also set the secret so webhook verification works
    monkeypatch.setenv("PAYSTACK_SECRET_KEY", "test_secret")
    from app.config import get_settings

    get_settings.cache_clear()
    yield client
    app.dependency_overrides.pop(billing_api.get_billing_client, None)
    get_settings.cache_clear()


# ----- Catalog ---------------------------------------------------------------


class TestCatalog:
    def test_catalog_has_all_currency_x_tier_combos(self):
        # 3 paid tiers x 5 currencies = 15 plans
        assert len(CATALOG) == 15

    def test_get_plan_resolves_correctly(self):
        from app.models import BillingInterval

        plan = get_plan(
            tier=SubscriptionTier.GROWTH,
            currency=BillingCurrency.NGN,
            interval=BillingInterval.MONTHLY,
        )
        assert plan is not None
        assert plan.amount_minor == 100_000_00  # ₦100,000
        assert plan.amount_major == 100_000.0

    def test_plans_for_currency_returns_only_one_currency(self):
        plans = plans_for_currency(BillingCurrency.NGN)
        assert len(plans) == 3  # starter, growth, audit_ready
        for p in plans:
            assert p.currency == BillingCurrency.NGN

    def test_lookup_keys_are_unique(self):
        keys = {p.lookup_key for p in CATALOG}
        assert len(keys) == len(CATALOG)


# ----- Country -> currency mapping ------------------------------------------


class TestCurrencyMapping:
    def test_signup_in_nigeria_sets_ngn(self, client, signup_payload, db_session):
        client.post("/api/v1/auth/signup", json=signup_payload)
        company = (
            db_session.query(Company)
            .filter(Company.country == "NG")
            .first()
        )
        assert company is not None
        assert company.billing_currency == BillingCurrency.NGN

    def test_signup_in_kenya_sets_kes(self, client, signup_payload, db_session):
        signup_payload["country"] = "KE"
        signup_payload["email"] = "k@example.com"
        signup_payload["company_name"] = "Kenyan Co"
        client.post("/api/v1/auth/signup", json=signup_payload)
        company = (
            db_session.query(Company).filter(Company.country == "KE").first()
        )
        assert company.billing_currency == BillingCurrency.KES

    def test_signup_in_unsupported_country_falls_back_to_usd(
        self, client, signup_payload, db_session
    ):
        signup_payload["country"] = "BR"  # Brazil — not in our market map
        signup_payload["email"] = "br@example.com"
        signup_payload["company_name"] = "Brazil Co"
        client.post("/api/v1/auth/signup", json=signup_payload)
        company = (
            db_session.query(Company).filter(Company.country == "BR").first()
        )
        assert company.billing_currency == BillingCurrency.USD


# ----- Licence gate ----------------------------------------------------------


class TestLicenceGate:
    def test_free_tier_requires_licence_for_assessments(self, free_tier_client):
        resp = free_tier_client.post("/api/v1/assessments", json={})
        assert resp.status_code == 402
        detail = resp.json()["detail"]
        assert detail["error"] == "license_required"
        assert detail["current_tier"] == "free"

    def test_free_tier_requires_licence_for_evidence(self, free_tier_client):
        resp = free_tier_client.post(
            "/api/v1/evidence",
            json={
                "title": "Access review",
                "kind": "narrative",
                "framework_code": "soc2",
                "control_code": "CC6.1",
                "narrative_text": "We do this.",
            },
        )
        assert resp.status_code == 402
        assert resp.json()["detail"]["error"] == "license_required"

    def test_free_tier_requires_licence_for_policies(self, free_tier_client):
        resp = free_tier_client.post(
            "/api/v1/policies",
            json={"template_code": "information_security"},
        )
        assert resp.status_code == 402
        assert resp.json()["detail"]["error"] == "license_required"

    def test_free_tier_can_still_view_billing(self, free_tier_client):
        pricing = free_tier_client.get("/api/v1/billing/pricing")
        assert pricing.status_code == 200
        subscription = free_tier_client.get("/api/v1/billing/subscription")
        assert subscription.status_code == 200

    def test_growth_tier_allows_unlimited(self, authed_client):
        # authed_client fixture upgrades to GROWTH
        for i in range(5):
            r = authed_client.post(
                "/api/v1/evidence",
                json={
                    "title": f"E{i}",
                    "kind": "narrative",
                    "framework_code": "soc2",
                    "control_code": "CC6.1",
                    "narrative_text": "We do this.",
                },
            )
            assert r.status_code == 201, f"Item {i} blocked at {r.status_code}"


# ----- Pricing endpoint ------------------------------------------------------


class TestPricingEndpoint:
    def test_pricing_returns_only_company_currency(self, authed_client):
        resp = authed_client.get("/api/v1/billing/pricing")
        assert resp.status_code == 200
        body = resp.json()
        # Nigerian default signup -> NGN
        assert body["currency"] == "NGN"
        assert body["free"]["tier"] == "free"
        assert body["free"]["amount_minor"] == 0
        for plan in body["paid"]:
            assert plan["currency"] == "NGN"
        assert len(body["paid"]) == 3

    def test_pricing_for_kenyan_company(self, client, db_session):
        signup = {
            "email": "k@example.com",
            "password": "Str0ngPassword!",
            "full_name": "Test User",
            "company_name": "Kenyan Co",
            "country": "KE",
            "sector": "fintech",
            "size": "small",
            "stage": "seed",
        }
        resp = client.post("/api/v1/auth/signup", json=signup)
        client.headers.update(
            {"Authorization": f"Bearer {resp.json()['tokens']['access_token']}"}
        )
        body = client.get("/api/v1/billing/pricing").json()
        assert body["currency"] == "KES"


# ----- Subscription state ----------------------------------------------------


class TestSubscriptionState:
    def test_default_subscription_is_free(self, authed_client, db_session):
        # Override the GROWTH upgrade for this specific test
        from app.models import Company

        company = db_session.query(Company).first()
        company.subscription_tier = SubscriptionTier.FREE
        db_session.commit()

        resp = authed_client.get("/api/v1/billing/subscription")
        assert resp.status_code == 200
        body = resp.json()
        assert body["tier"] == "free"
        assert body["active_subscription"] is None


# ----- Webhook signature -----------------------------------------------------


class TestWebhookSigning:
    def test_correct_signature_verifies(self):
        body = b'{"event":"charge.success","data":{}}'
        secret = "sk_test_secret_key"
        sig = compute_paystack_signature(raw_body=body, secret_key=secret)
        assert verify_paystack_signature(
            raw_body=body, signature_header=sig, secret_key=secret
        )

    def test_wrong_signature_rejected(self):
        body = b'{"event":"charge.success","data":{}}'
        secret = "sk_test_secret_key"
        assert not verify_paystack_signature(
            raw_body=body,
            signature_header="0" * 128,
            secret_key=secret,
        )

    def test_tampered_body_rejected(self):
        body = b'{"event":"charge.success","data":{}}'
        secret = "sk_test_secret_key"
        sig = compute_paystack_signature(raw_body=body, secret_key=secret)
        tampered = b'{"event":"charge.success","data":{"hijacked":true}}'
        assert not verify_paystack_signature(
            raw_body=tampered, signature_header=sig, secret_key=secret
        )

    def test_missing_signature_rejected(self):
        assert not verify_paystack_signature(
            raw_body=b"{}", signature_header=None, secret_key="x"
        )

    def test_missing_secret_fails_closed(self):
        sig = compute_paystack_signature(raw_body=b"{}", secret_key="x")
        # Server has no secret configured: even a valid-looking sig is rejected.
        assert not verify_paystack_signature(
            raw_body=b"{}", signature_header=sig, secret_key=""
        )


# ----- Mock Paystack client --------------------------------------------------


class TestMockPaystackClient:
    def test_upsert_plan_is_idempotent(self):
        client = MockPaystackClient()
        a = client.upsert_plan(
            name="Test Plan",
            amount_minor=10000,
            currency="NGN",
        )
        b = client.upsert_plan(
            name="Test Plan",
            amount_minor=10000,
            currency="NGN",
        )
        assert a.plan_code == b.plan_code

    def test_initialize_transaction_returns_url(self):
        client = MockPaystackClient()
        init = client.initialize_transaction(
            email="x@example.com",
            amount_minor=10000,
            currency="NGN",
            plan_code="PLN_test",
        )
        assert init.authorization_url.startswith("https://")
        assert init.reference.startswith("ref_mock_")

    def test_disable_subscription_marks_cancelled(self):
        client = MockPaystackClient()
        sub = client._seed_subscription(
            subscription_code="SUB_test",
            email_token="tok",
            customer_code="CUS_test",
            plan_code="PLN_test",
        )
        client.disable_subscription("SUB_test", "tok")
        assert client.fetch_subscription("SUB_test").status == "cancelled"

    def test_fetch_unknown_subscription_raises(self):
        client = MockPaystackClient()
        with pytest.raises(PaystackError):
            client.fetch_subscription("nope")


# ----- Checkout flow end-to-end ---------------------------------------------


class TestCheckoutFlow:
    def test_checkout_returns_authorization_url(
        self, authed_client, mock_paystack
    ):
        resp = authed_client.post(
            "/api/v1/billing/checkout",
            json={"tier": "growth"},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["authorization_url"].startswith("https://")
        assert body["subscription_id"]
        assert body["reference"].startswith("ref_mock_")

    def test_free_tier_can_start_checkout_for_paid_licence(
        self, free_tier_client, mock_paystack
    ):
        resp = free_tier_client.post(
            "/api/v1/billing/checkout",
            json={"tier": "starter"},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["authorization_url"].startswith("https://")

    def test_cannot_checkout_for_free(self, authed_client, mock_paystack):
        resp = authed_client.post(
            "/api/v1/billing/checkout",
            json={"tier": "free"},
        )
        assert resp.status_code == 400


# ----- Webhook event processing ---------------------------------------------


class TestWebhookProcessing:
    def _post_webhook(
        self, client, payload: dict, secret: str = "test_secret"
    ):
        body = json.dumps(payload).encode("utf-8")
        sig = compute_paystack_signature(raw_body=body, secret_key=secret)
        return client.post(
            "/api/v1/billing/webhook",
            content=body,
            headers={
                "x-paystack-signature": sig,
                "content-type": "application/json",
            },
        )

    def test_invalid_signature_returns_401(self, client, mock_paystack):
        resp = client.post(
            "/api/v1/billing/webhook",
            content=b'{"event":"charge.success","data":{}}',
            headers={"x-paystack-signature": "0" * 128},
        )
        assert resp.status_code == 401

    def test_missing_signature_header_returns_401(self, client, mock_paystack):
        resp = client.post(
            "/api/v1/billing/webhook",
            content=b'{"event":"charge.success","data":{}}',
        )
        assert resp.status_code == 401

    def test_subscription_create_activates_company(
        self, authed_client, client, db_session, mock_paystack
    ):
        co = authed_client.post(
            "/api/v1/billing/checkout",
            json={"tier": "growth"},
        ).json()
        sub_id = co["subscription_id"]

        payload = {
            "event": "subscription.create",
            "data": {
                "subscription_code": "SUB_paystack_test",
                "email_token": "tok_xyz",
                "customer": {
                    "customer_code": "CUS_paystack_test",
                    "email": "founder@acmefintech.ng",
                },
                "plan": {"plan_code": "PLN_test"},
                "metadata": {
                    "subscription_id": sub_id,
                    "tier": "growth",
                },
            },
        }
        resp = self._post_webhook(client, payload, secret="test_secret")
        assert resp.status_code == 200, resp.text

        sub = (
            db_session.query(Subscription)
            .filter(Subscription.id == sub_id)
            .first()
        )
        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.paystack_subscription_code == "SUB_paystack_test"

        company = (
            db_session.query(Company).filter(Company.id == sub.company_id).first()
        )
        assert company.subscription_tier == SubscriptionTier.GROWTH

    def test_subscription_disable_downgrades_to_free(
        self, authed_client, client, db_session, mock_paystack
    ):
        co = authed_client.post(
            "/api/v1/billing/checkout", json={"tier": "growth"}
        ).json()
        sub_id = co["subscription_id"]

        self._post_webhook(
            client,
            {
                "event": "subscription.create",
                "data": {
                    "subscription_code": "SUB_active",
                    "email_token": "tok",
                    "customer": {"customer_code": "CUS_x"},
                    "plan": {"plan_code": "PLN_x"},
                    "metadata": {"subscription_id": sub_id},
                },
            },
            secret="test_secret",
        )

        resp = self._post_webhook(
            client,
            {
                "event": "subscription.disable",
                "data": {"subscription_code": "SUB_active"},
            },
            secret="test_secret",
        )
        assert resp.status_code == 200

        sub = (
            db_session.query(Subscription)
            .filter(Subscription.id == sub_id)
            .first()
        )
        assert sub.status == SubscriptionStatus.CANCELLED

        company = (
            db_session.query(Company).filter(Company.id == sub.company_id).first()
        )
        assert company.subscription_tier == SubscriptionTier.FREE

    def test_duplicate_webhook_acked_but_not_reprocessed(
        self, authed_client, client, db_session, mock_paystack
    ):
        from app.models import BillingEvent

        co = authed_client.post(
            "/api/v1/billing/checkout", json={"tier": "growth"}
        ).json()

        payload = {
            "event": "subscription.create",
            "data": {
                "subscription_code": "SUB_dupe_test",
                "email_token": "tok",
                "customer": {"customer_code": "CUS_x"},
                "plan": {"plan_code": "PLN_x"},
                "metadata": {"subscription_id": co["subscription_id"]},
            },
        }

        first = self._post_webhook(client, payload, secret="test_secret")
        assert first.status_code == 200
        assert first.json()["status"] == "ok"

        second = self._post_webhook(client, payload, secret="test_secret")
        assert second.status_code == 200
        assert second.json()["status"] == "duplicate"

        events = (
            db_session.query(BillingEvent)
            .filter(BillingEvent.raw_event_name == "subscription.create")
            .all()
        )
        assert len(events) == 1

    def test_unknown_event_logged_but_not_acted_on(
        self, client, db_session, mock_paystack
    ):
        from app.models import BillingEvent

        resp = self._post_webhook(
            client,
            {"event": "transfer.success", "data": {"id": 12345}},
            secret="test_secret",
        )
        assert resp.status_code == 200

        event = (
            db_session.query(BillingEvent)
            .filter(BillingEvent.raw_event_name == "transfer.success")
            .first()
        )
        assert event is not None
        assert event.processed is True
