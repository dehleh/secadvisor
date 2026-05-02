"""Paystack webhook signature verification.

Paystack signs every webhook with HMAC-SHA512 over the raw request body
using your secret key, sent as the x-paystack-signature header. We verify
on every webhook before doing anything with the payload — an unverified
"webhook" is just a stranger sending us JSON.

Reference: https://paystack.com/docs/payments/webhooks/#verify-event-origin
"""
from __future__ import annotations

import hashlib
import hmac


def verify_paystack_signature(
    *,
    raw_body: bytes,
    signature_header: str | None,
    secret_key: str,
) -> bool:
    """Return True if the signature header matches an HMAC-SHA512 of the body.

    Constant-time comparison via hmac.compare_digest to prevent timing
    side channels.
    """
    if not signature_header:
        return False
    if not secret_key:
        # Misconfigured environment — fail closed rather than fail open.
        return False

    computed = hmac.new(
        key=secret_key.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha512,
    ).hexdigest()

    return hmac.compare_digest(computed, signature_header)


def compute_paystack_signature(*, raw_body: bytes, secret_key: str) -> str:
    """Helper for tests: produce the signature header for a given body."""
    return hmac.new(
        key=secret_key.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha512,
    ).hexdigest()
