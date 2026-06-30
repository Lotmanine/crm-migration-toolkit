"""Canonical, platform-agnostic contact model.

Every source platform (Mailchimp, ActiveCampaign, Klaviyo, ...) gets mapped
INTO this shape, and every target platform gets written FROM it. Keeping one
normalized model in the middle is what makes a migration auditable: counts,
consent, and custom fields all reconcile against a single schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# Consent status drives whether a contact is mailable on the target platform.
CONSENT_SUBSCRIBED = "subscribed"
CONSENT_UNSUBSCRIBED = "unsubscribed"
CONSENT_PENDING = "pending"
CONSENT_CLEANED = "cleaned"  # hard-bounced / invalid on the source platform

VALID_CONSENT = {
    CONSENT_SUBSCRIBED,
    CONSENT_UNSUBSCRIBED,
    CONSENT_PENDING,
    CONSENT_CLEANED,
}


@dataclass
class Contact:
    """One normalized contact.

    `consent_provenance` is deliberately a free-text audit string (where the
    consent came from + when + on which system). Regulators and the receiving
    ESP both care about provenance, and it is the field most migrations lose.
    """

    email: str
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    consent_status: str = CONSENT_PENDING
    consent_provenance: str = ""
    tags: list[str] = field(default_factory=list)
    custom_fields: dict[str, str] = field(default_factory=dict)
    source_id: str = ""  # original ID on the source platform, for traceability

    def is_mailable(self) -> bool:
        return self.consent_status == CONSENT_SUBSCRIBED
