"""Flutterwave webhook signature verification.

Flutterwave signs webhooks with HMAC-SHA256 over the raw request body using
the webhook secret hash from the dashboard, sent as the flutterwave-signature
header. We verify on every webhook before doing anything with the payload.

Reference: https://developer.flutterwave.com/docs/webhooks
"""
from __future__ import annotations

import base64
import hashlib
import hmac


def verify_flutterwave_signature(
    *,
    raw_body: bytes,
    signature_header: str | None,
    secret_hash: str,
) -> bool:
    """Return True if the signature header matches an HMAC-SHA256 of the body."""
    if not signature_header:
        return False
    if not secret_hash:
        return False

    digest = hmac.new(
        key=secret_hash.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).digest()
    computed = base64.b64encode(digest).decode("utf-8")

    return hmac.compare_digest(computed, signature_header)


def compute_flutterwave_signature(*, raw_body: bytes, secret_hash: str) -> str:
    """Helper for tests: produce the signature header for a given body."""
    digest = hmac.new(
        key=secret_hash.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("utf-8")
