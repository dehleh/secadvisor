"""Company-email policy.

We only accept work / company email addresses for signup, login, and team
invites. Free webmail providers (gmail, yahoo, hotmail, etc.) are rejected
so that every account is tied to a verifiable organisation domain.
"""
from __future__ import annotations

# Curated list of public/free email providers that are NOT accepted.
# Lowercase, exact-match on the domain portion of the address.
FREE_EMAIL_DOMAINS: frozenset[str] = frozenset(
    {
        # Global
        "gmail.com",
        "googlemail.com",
        "yahoo.com",
        "yahoo.co.uk",
        "yahoo.co.in",
        "ymail.com",
        "rocketmail.com",
        "hotmail.com",
        "hotmail.co.uk",
        "outlook.com",
        "live.com",
        "msn.com",
        "icloud.com",
        "me.com",
        "mac.com",
        "aol.com",
        "protonmail.com",
        "proton.me",
        "pm.me",
        "gmx.com",
        "gmx.de",
        "mail.com",
        "zoho.com",
        "yandex.com",
        "yandex.ru",
        "fastmail.com",
        "tutanota.com",
        "tuta.io",
        "qq.com",
        "163.com",
        "126.com",
        "naver.com",
        "hey.com",
        # Disposable / temporary
        "mailinator.com",
        "guerrillamail.com",
        "10minutemail.com",
        "tempmail.com",
        "trashmail.com",
        "yopmail.com",
        "throwawaymail.com",
        "sharklasers.com",
        "getnada.com",
        # Africa-region free providers occasionally used in lieu of work email
        "yahoo.fr",
        "rediffmail.com",
        "webmail.co.za",
    }
)


class FreeEmailNotAllowedError(ValueError):
    """Raised when a signup/login/invite uses a non-company email."""


def assert_company_email(email: str) -> str:
    """Validate that ``email`` is a company / work address.

    Returns the normalised (lower-cased) email on success. Raises
    :class:`FreeEmailNotAllowedError` (a ``ValueError``) otherwise so it
    integrates cleanly with Pydantic field validators.
    """
    if not email or "@" not in email:
        # Let EmailStr handle the basic format error; this branch is defensive.
        raise FreeEmailNotAllowedError("Invalid email address.")
    normalised = email.strip().lower()
    domain = normalised.rsplit("@", 1)[1]
    if domain in FREE_EMAIL_DOMAINS:
        raise FreeEmailNotAllowedError(
            "Please sign up with your company email address. "
            "Free webmail providers (e.g. Gmail, Yahoo, Outlook) are not accepted."
        )
    return normalised
