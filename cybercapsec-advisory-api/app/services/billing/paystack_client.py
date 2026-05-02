"""Paystack API client.

Two implementations behind one interface:

  PaystackClient (real)   — calls api.paystack.co
  MockPaystackClient      — deterministic, no network, used in dev and tests

Selection is via the USE_MOCK_PAYMENTS env flag, mirroring the AI
advisor's USE_MOCK_AI seam from Session 3. Tests never hit the network.

Paystack API reference: https://paystack.com/docs/api/
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


# ----- DTOs ------------------------------------------------------------------


@dataclass(frozen=True)
class PaystackPlan:
    plan_code: str
    name: str
    amount_minor: int
    interval: str  # "monthly", "annually", "weekly", etc.
    currency: str


@dataclass(frozen=True)
class PaystackTransactionInit:
    """Returned by /transaction/initialize. Contains the URL we redirect to."""
    authorization_url: str
    access_code: str
    reference: str


@dataclass(frozen=True)
class PaystackSubscription:
    subscription_code: str
    email_token: str
    customer_code: str
    plan_code: str
    status: str
    amount_minor: int
    next_payment_date: str | None


# ----- Interface -------------------------------------------------------------


class PaystackClientBase(ABC):
    """Abstraction over the bits of Paystack's API we use."""

    @abstractmethod
    def upsert_plan(
        self,
        *,
        name: str,
        amount_minor: int,
        currency: str,
        interval: str = "monthly",
        description: str | None = None,
    ) -> PaystackPlan: ...

    @abstractmethod
    def initialize_transaction(
        self,
        *,
        email: str,
        amount_minor: int,
        currency: str,
        plan_code: str | None = None,
        callback_url: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PaystackTransactionInit: ...

    @abstractmethod
    def fetch_subscription(self, subscription_code: str) -> PaystackSubscription: ...

    @abstractmethod
    def disable_subscription(
        self, subscription_code: str, email_token: str
    ) -> None: ...


# ----- Real implementation ---------------------------------------------------


class PaystackClient(PaystackClientBase):
    """Calls the live Paystack API."""

    BASE_URL = "https://api.paystack.co"

    def __init__(self, secret_key: str, *, timeout: float = 10.0):
        if not secret_key:
            raise ValueError("Paystack secret key is required")
        self._secret_key = secret_key
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._secret_key}",
            "Content-Type": "application/json",
        }

    def _post(self, path: str, payload: dict) -> dict:
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(
                f"{self.BASE_URL}{path}",
                json=payload,
                headers=self._headers(),
            )
        return self._parse(resp)

    def _get(self, path: str) -> dict:
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.get(f"{self.BASE_URL}{path}", headers=self._headers())
        return self._parse(resp)

    def _parse(self, resp: httpx.Response) -> dict:
        # Paystack returns 2xx with {"status": true, "message": "...", "data": {...}}
        # On error: 4xx/5xx with the same shape but status: false.
        if resp.status_code >= 500:
            raise PaystackError(
                f"Paystack server error {resp.status_code}: {resp.text[:300]}"
            )
        try:
            body = resp.json()
        except ValueError as exc:
            raise PaystackError(f"Non-JSON Paystack response: {resp.text[:300]}") from exc
        if not body.get("status", False):
            raise PaystackError(
                f"Paystack API error: {body.get('message', 'unknown')}",
                response_body=body,
            )
        return body.get("data", {})

    def upsert_plan(
        self,
        *,
        name: str,
        amount_minor: int,
        currency: str,
        interval: str = "monthly",
        description: str | None = None,
    ) -> PaystackPlan:
        # Paystack doesn't have native upsert; create + ignore "plan name exists"
        # is the standard pattern. We list first to find an existing match.
        existing = self._get(f"/plan?name={name}")
        if isinstance(existing, list):
            for plan in existing:
                if plan.get("name") == name and plan.get("currency") == currency:
                    return PaystackPlan(
                        plan_code=plan["plan_code"],
                        name=plan["name"],
                        amount_minor=plan["amount"],
                        interval=plan["interval"],
                        currency=plan["currency"],
                    )

        data = self._post(
            "/plan",
            {
                "name": name,
                "amount": amount_minor,
                "interval": interval,
                "currency": currency,
                "description": description,
            },
        )
        return PaystackPlan(
            plan_code=data["plan_code"],
            name=data["name"],
            amount_minor=data["amount"],
            interval=data["interval"],
            currency=data["currency"],
        )

    def initialize_transaction(
        self,
        *,
        email: str,
        amount_minor: int,
        currency: str,
        plan_code: str | None = None,
        callback_url: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PaystackTransactionInit:
        payload: dict[str, Any] = {
            "email": email,
            "amount": amount_minor,
            "currency": currency,
        }
        if plan_code:
            payload["plan"] = plan_code
        if callback_url:
            payload["callback_url"] = callback_url
        if metadata:
            payload["metadata"] = metadata

        data = self._post("/transaction/initialize", payload)
        return PaystackTransactionInit(
            authorization_url=data["authorization_url"],
            access_code=data["access_code"],
            reference=data["reference"],
        )

    def fetch_subscription(self, subscription_code: str) -> PaystackSubscription:
        data = self._get(f"/subscription/{subscription_code}")
        return PaystackSubscription(
            subscription_code=data["subscription_code"],
            email_token=data["email_token"],
            customer_code=data["customer"]["customer_code"],
            plan_code=data["plan"]["plan_code"],
            status=data["status"],
            amount_minor=data["amount"],
            next_payment_date=data.get("next_payment_date"),
        )

    def disable_subscription(
        self, subscription_code: str, email_token: str
    ) -> None:
        self._post(
            "/subscription/disable",
            {"code": subscription_code, "token": email_token},
        )


# ----- Mock implementation ---------------------------------------------------


class MockPaystackClient(PaystackClientBase):
    """Deterministic in-memory client for dev and tests.

    Generates plan codes, subscription codes, and transaction refs that
    look real enough for end-to-end testing without hitting the network.
    All state lives in instance dicts — tests get a fresh instance.
    """

    def __init__(self):
        self._plans: dict[str, PaystackPlan] = {}
        self._subscriptions: dict[str, PaystackSubscription] = {}
        self._counter = 0

    def _next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}_mock_{self._counter:08d}"

    def upsert_plan(
        self,
        *,
        name: str,
        amount_minor: int,
        currency: str,
        interval: str = "monthly",
        description: str | None = None,
    ) -> PaystackPlan:
        # Match by (name, currency) like the real impl
        for plan in self._plans.values():
            if plan.name == name and plan.currency == currency:
                return plan
        plan_code = self._next_id("PLN")
        plan = PaystackPlan(
            plan_code=plan_code,
            name=name,
            amount_minor=amount_minor,
            interval=interval,
            currency=currency,
        )
        self._plans[plan_code] = plan
        return plan

    def initialize_transaction(
        self,
        *,
        email: str,
        amount_minor: int,
        currency: str,
        plan_code: str | None = None,
        callback_url: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PaystackTransactionInit:
        ref = self._next_id("ref")
        access_code = self._next_id("ac")
        return PaystackTransactionInit(
            authorization_url=f"https://checkout.paystack.com/mock/{access_code}",
            access_code=access_code,
            reference=ref,
        )

    def fetch_subscription(self, subscription_code: str) -> PaystackSubscription:
        sub = self._subscriptions.get(subscription_code)
        if sub is None:
            raise PaystackError(f"Mock subscription not found: {subscription_code}")
        return sub

    def disable_subscription(
        self, subscription_code: str, email_token: str
    ) -> None:
        sub = self._subscriptions.get(subscription_code)
        if sub is None:
            return
        self._subscriptions[subscription_code] = PaystackSubscription(
            subscription_code=sub.subscription_code,
            email_token=sub.email_token,
            customer_code=sub.customer_code,
            plan_code=sub.plan_code,
            status="cancelled",
            amount_minor=sub.amount_minor,
            next_payment_date=None,
        )

    # ---- Test helpers -------------------------------------------------------

    def _seed_subscription(
        self,
        *,
        subscription_code: str,
        email_token: str,
        customer_code: str,
        plan_code: str,
        status: str = "active",
        amount_minor: int = 0,
    ) -> PaystackSubscription:
        sub = PaystackSubscription(
            subscription_code=subscription_code,
            email_token=email_token,
            customer_code=customer_code,
            plan_code=plan_code,
            status=status,
            amount_minor=amount_minor,
            next_payment_date=None,
        )
        self._subscriptions[subscription_code] = sub
        return sub


# ----- Errors ----------------------------------------------------------------


class PaystackError(Exception):
    """Raised when Paystack returns an error or behaves unexpectedly."""

    def __init__(self, message: str, *, response_body: dict | None = None):
        super().__init__(message)
        self.response_body = response_body or {}


# ----- Factory ---------------------------------------------------------------


def get_paystack_client(
    *,
    use_mock: bool,
    secret_key: str | None,
) -> PaystackClientBase:
    """Resolve the Paystack client based on config.

    Tests should pass use_mock=True. Production passes use_mock=False with
    a real secret_key.
    """
    if use_mock:
        return MockPaystackClient()
    if not secret_key:
        raise ValueError(
            "Paystack secret key required when USE_MOCK_PAYMENTS is false"
        )
    return PaystackClient(secret_key)
