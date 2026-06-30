"""The migration pipeline: extract -> transform -> suppress -> dedupe -> load.

Each stage returns its rejects instead of dropping them silently, so the
integrity report can reconcile every input row to exactly one outcome:

    source_rows == loaded + suppressed + invalid + duplicates
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field

from .mapping import Mapping
from .models import Contact
from .normalize import normalize_consent, normalize_email, normalize_phone


@dataclass
class MigrationResult:
    loaded: list[Contact] = field(default_factory=list)
    suppressed: list[Contact] = field(default_factory=list)
    invalid: list[dict] = field(default_factory=list)      # rows with no usable email
    duplicates: list[Contact] = field(default_factory=list)
    source_rows: int = 0


def _read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def load_suppression(path: str) -> set[str]:
    """Suppression list -> set of normalized emails. Accepts a 1-column CSV
    (header 'email') or a plain newline list."""
    emails: set[str] = set()
    for row in _read_csv(path):
        value = row.get("email") or next(iter(row.values()), "")
        normalized = normalize_email(value)
        if normalized:
            emails.add(normalized)
    return emails


def _to_contact(row: dict, mapping: Mapping) -> Contact | None:
    email = normalize_email(row.get(_src(mapping, "email"), ""))
    if not email:
        return None

    contact = Contact(email=email)
    for src_col, attr in mapping.standard.items():
        if attr in ("email",):
            continue
        value = (row.get(src_col) or "").strip()
        if attr == "phone":
            value = normalize_phone(value)
        setattr(contact, attr, value)

    for src_col, key in mapping.custom.items():
        value = (row.get(src_col) or "").strip()
        if value:
            contact.custom_fields[key] = value

    if mapping.tags_column:
        raw_tags = row.get(mapping.tags_column, "") or ""
        contact.tags = [t.strip() for t in raw_tags.split(mapping.tags_delimiter) if t.strip()]

    contact.consent_status = normalize_consent(row.get(mapping.consent_status_column, ""))
    consent_date = (row.get(mapping.consent_date_column, "") or "").strip() or "date unknown"
    contact.consent_provenance = (
        f"imported from {mapping.source_system}; "
        f"source status '{(row.get(mapping.consent_status_column) or '').strip() or 'n/a'}' "
        f"as of {consent_date}"
    )
    contact.source_id = (row.get("id") or row.get("ID") or "").strip()
    return contact


def _src(mapping: Mapping, attr: str) -> str:
    """Find the source column that maps to a given canonical attribute."""
    for col, target in mapping.standard.items():
        if target == attr:
            return col
    return ""


def run(source_csv: str, mapping: Mapping, suppression_csv: str | None = None) -> MigrationResult:
    rows = _read_csv(source_csv)
    suppression = load_suppression(suppression_csv) if suppression_csv else set()

    result = MigrationResult(source_rows=len(rows))
    seen: set[str] = set()

    for row in rows:
        contact = _to_contact(row, mapping)
        if contact is None:
            result.invalid.append(row)
            continue
        if contact.email in seen:
            result.duplicates.append(contact)
            continue
        seen.add(contact.email)
        if contact.email in suppression:
            result.suppressed.append(contact)
            continue
        result.loaded.append(contact)

    return result


# ---- target writer (FluentCRM-shaped CSV; swap for any ESP import format) ----

_TARGET_HEADERS = [
    "email", "first_name", "last_name", "phone",
    "status", "tags", "consent_provenance", "source_id",
]


def write_target_csv(contacts: list[Contact], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(_TARGET_HEADERS)
        for c in contacts:
            writer.writerow([
                c.email, c.first_name, c.last_name, c.phone,
                c.consent_status, "|".join(c.tags),
                c.consent_provenance, c.source_id,
            ])
