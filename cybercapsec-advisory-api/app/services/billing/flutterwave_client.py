"""Flutterwave API client.

Two implementations behind one interface:

  FlutterwaveClient (real)   - calls api.flutterwave.com
  MockFlutterwaveClient      - deterministic, no network, used in dev and tests

Flutterwave API reference: https://developer.flutterwave.com/
"""
from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FlutterwavePlan:
    plan_code: str
    name: str
    amount_minor: int
    interval: str
    currency: str


@dataclass(frozen=True)
class FlutterwaveTransactionInit:
    """Returned by /v3/payments. Contains the URL we redirect to."""

    authorization_url: str
    access_code: str
    reference: str


@dataclass(frozen=True)
class FlutterwaveSubscription:
    subscription_code: str
    email_token: str | None
    customer_code: str | None
    plan_code: str | None
    status: str
    amount_minor: int
    next_payment_date: str | None


class FlutterwaveClientBase(ABC):
    """Abstraction over the bits of Flutterwave's API we use."""

    @abstractmethod
    def upsert_plan(
        self,
        *,
        name: str,
        amount_minor: int,
        currency: str,
        interval: str = "monthly",
        description: str | None = None,
    ) -> FlutterwavePlan: ...

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
    ) -> FlutterwaveTransactionInit: ...

    @abstractmethod
    def fetch_subscription(self, subscription_code: str) -> FlutterwaveSubscription: ...

    @abstractmethod
    def disable_subscription(
        self, subscription_code: str, email_token: str | None = None
    ) -> None: ...


class FlutterwaveClient(FlutterwaveClientBase):
    """Calls the live Flutterwave API."""

    BASE_URL = "https://api.flutterwave.com/v3"

    def __init__(self, secret_key: str, *, timeout: float = 10.0):
        if not secret_key:
            raise ValueError("Flutterwave secret key is required")
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

    def _put(self, path: str, payload: dict | None = None) -> dict:
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.put(
                f"{self.BASE_URL}{path}",
                json=payload or {},
                headers=self._headers(),
            )
        return self._parse(resp)

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> dict | list:
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.get(
                f"{self.BASE_URL}{path}",
                params=params,
                headers=self._headers(),
            )
        return self._parse(resp)

    def _parse(self, resp: httpx.Response) -> dict | list:
        if resp.status_code >= 500:
            raise FlutterwaveError(
                f"Flutterwave server error {resp.status_code}: {resp.text[:300]}"
            )
        try:
            body = resp.json()
        except ValueError as exc:
            raise FlutterwaveError(
                f"Non-JSON Flutterwave response: {resp.text[:300]}"
            ) from exc
        if body.get("status") != "success":
            raise FlutterwaveError(
                f"Flutterwave API error: {body.get('message', 'unknown')}",
                response_body=body,
            )
        return body.get("data", {})

    @staticmethod
    def _amount_major(amount_minor: int) -> int | float:
        amount = amount_minor / 100
        return int(amount) if amount.is_integer() else amount

    @staticmethod
    def _amount_minor(amount_major: int | float | str | None) -> int:
        if amount_major is None:
            return 0
        return int(float(amount_major) * 100)

    def upsert_plan(
        self,
        *,
        name: str,
        amount_minor: int,
        currency: str,
        interval: str = "monthly",
        description: str | None = None,
    ) -> FlutterwavePlan:
        amount_major = self._amount_major(amount_minor)
        existing = self._get(
            "/payment-plans",
            params={
                "amount": amount_major,
                "currency": currency,
                "interval": interval,
                "status": "active",
            },
        )
        candidates = existing if isinstance(existing, list) else existing.get("plans", [])
        for plan in candidates:
            if (
                str(plan.get("name")) == name
                and str(plan.get("currency", currency)).upper() == currency
                and str(plan.get("interval")) == interval
                and self._amount_minor(plan.get("amount")) == amount_minor
            ):
                return FlutterwavePlan(
                    plan_code=str(plan["id"]),
                    name=plan["name"],
                    amount_minor=amount_minor,
                    interval=plan["interval"],
                    currency=currency,
                )

        data = self._post(
            "/payment-plans",
            {
                "name": name,
                "amount": amount_major,
                "interval": interval,
                "currency": currency,
            },
        )
        return FlutterwavePlan(
            plan_code=str(data["id"]),
            name=data["name"],
            amount_minor=self._amount_minor(data.get("amount", amount_major)),
            interval=data["interval"],
            currency=data.get("currency", currency),
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
    ) -> FlutterwaveTransactionInit:
        tx_ref = str(metadata.get("subscription_id")) if metadata else uuid.uuid4().hex
        payload: dict[str, Any] = {
            "tx_ref": tx_ref,
            "amount": self._amount_major(amount_minor),
            "currency": currency,
            "customer": {"email": email},
            "customizations": {
                "title": "CyberCapSec Advisory",
                "description": "Monthly subscription",
            },
        }
        if plan_code:
            payload["payment_plan"] = int(plan_code) if plan_code.isdigit() else plan_code
        if callback_url:
            payload["redirect_url"] = callback_url
        if metadata:
            payload["meta"] = metadata

        data = self._post("/payments", payload)
        link = data["link"]
        return FlutterwaveTransactionInit(
            authorization_url=link,
            access_code=link.rsplit("/", 1)[-1],
            reference=tx_ref,
        )

    def fetch_subscription(self, subscription_code: str) -> FlutterwaveSubscription:
        data = self._get(f"/subscriptions/{subscription_code}")
        return FlutterwaveSubscription(
            subscription_code=str(data["id"]),
            email_token=None,
            customer_code=str((data.get("customer") or {}).get("id", "")) or None,
            plan_code=str(data.get("plan")) if data.get("plan") is not None else None,
            status=data["status"],
            amount_minor=self._amount_minor(data.get("amount")),
            next_payment_date=data.get("next_due_date"),
        )

    def disable_subscription(
        self, subscription_code: str, email_token: str | None = None
    ) -> None:
        self._put(f"/subscriptions/{subscription_code}/cancel")


class MockFlutterwaveClient(FlutterwaveClientBase):
    """Deterministic in-memory client for dev and tests."""

    def __init__(self):
        self._plans: dict[str, FlutterwavePlan] = {}
        self._subscriptions: dict[str, FlutterwaveSubscription] = {}
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
    ) -> FlutterwavePlan:
        for plan in self._plans.values():
            if plan.name == name and plan.currency == currency:
                return plan
        plan_code = str(self._counter + 1000)
        self._counter += 1
        plan = FlutterwavePlan(
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
    ) -> FlutterwaveTransactionInit:
        ref = self._next_id("ref")
        access_code = self._next_id("flwlnk")
        return FlutterwaveTransactionInit(
            authorization_url=f"https://checkout.flutterwave.com/v3/hosted/pay/{access_code}",
            access_code=access_code,
            reference=ref,
        )

    def fetch_subscription(self, subscription_code: str) -> FlutterwaveSubscription:
        sub = self._subscriptions.get(subscription_code)
        if sub is None:
            raise FlutterwaveError(f"Mock subscription not found: {subscription_code}")
        return sub

    def disable_subscription(
        self, subscription_code: str, email_token: str | None = None
    ) -> None:
        sub = self._subscriptions.get(subscription_code)
        if sub is None:
            return
        self._subscriptions[subscription_code] = FlutterwaveSubscription(
            subscription_code=sub.subscription_code,
            email_token=sub.email_token,
            customer_code=sub.customer_code,
            plan_code=sub.plan_code,
            status="cancelled",
            amount_minor=sub.amount_minor,
            next_payment_date=None,
        )

    def _seed_subscription(
        self,
        *,
        subscription_code: str,
        email_token: str | None = None,
        customer_code: str | None = None,
        plan_code: str | None = None,
        status: str = "active",
        amount_minor: int = 0,
    ) -> FlutterwaveSubscription:
        sub = FlutterwaveSubscription(
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


class FlutterwaveError(Exception):
    """Raised when Flutterwave returns an error or behaves unexpectedly."""

    def __init__(self, message: str, *, response_body: dict | None = None):
        super().__init__(message)
        self.response_body = response_body or {}


def get_flutterwave_client(
    *,
    use_mock: bool,
    secret_key: str | None,
) -> FlutterwaveClientBase:
    if use_mock:
        return MockFlutterwaveClient()
    if not secret_key:
        raise ValueError(
            "Flutterwave secret key required when USE_MOCK_PAYMENTS is false"
        )
    return FlutterwaveClient(secret_key)
