"""Normalization helpers.

The single most common cause of "the counts don't match after migration" is
inconsistent email/consent normalization between extract and suppression. All
of it lives here so both paths use exactly the same rules.
"""

from __future__ import annotations

import re

from .models import (
    CONSENT_CLEANED,
    CONSENT_PENDING,
    CONSENT_SUBSCRIBED,
    CONSENT_UNSUBSCRIBED,
)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(raw: str) -> str:
    """Lowercase + trim. Returns '' if the value cannot be an email at all."""
    if not raw:
        return ""
    email = raw.strip().lower()
    return email if _EMAIL_RE.match(email) else ""


def normalize_phone(raw: str) -> str:
    """Keep a leading + and digits only. Empty string if nothing usable."""
    if not raw:
        return ""
    cleaned = re.sub(r"[^\d+]", "", raw.strip())
    cleaned = "+" + re.sub(r"\D", "", cleaned) if cleaned.startswith("+") else re.sub(r"\D", "", cleaned)
    return cleaned


# Map each source platform's status vocabulary onto our canonical statuses.
# Unknown values fall through to PENDING so we never silently mark someone
# mailable that the source did not.
_CONSENT_ALIASES = {
    "subscribed": CONSENT_SUBSCRIBED,
    "active": CONSENT_SUBSCRIBED,
    "confirmed": CONSENT_SUBSCRIBED,
    "unsubscribed": CONSENT_UNSUBSCRIBED,
    "unsub": CONSENT_UNSUBSCRIBED,
    "opted_out": CONSENT_UNSUBSCRIBED,
    "pending": CONSENT_PENDING,
    "unconfirmed": CONSENT_PENDING,
    "cleaned": CONSENT_CLEANED,
    "bounced": CONSENT_CLEANED,
    "invalid": CONSENT_CLEANED,
}


def normalize_consent(raw: str) -> str:
    return _CONSENT_ALIASES.get((raw or "").strip().lower(), CONSENT_PENDING)
