"""Post-migration integrity report.

This is the part most "migrations" skip and the part clients actually need:
proof that every source row is accounted for and that the mailable count on
the target matches what consent allows. If the reconciliation line does not
balance, the migration is wrong, full stop.
"""

from __future__ import annotations

from collections import Counter

from .models import CONSENT_SUBSCRIBED
from .pipeline import MigrationResult


def build_report(result: MigrationResult) -> str:
    accounted = (
        len(result.loaded)
        + len(result.suppressed)
        + len(result.invalid)
        + len(result.duplicates)
    )
    balanced = accounted == result.source_rows

    consent_breakdown = Counter(c.consent_status for c in result.loaded)
    mailable = sum(1 for c in result.loaded if c.consent_status == CONSENT_SUBSCRIBED)
    missing_provenance = sum(1 for c in result.loaded if not c.consent_provenance)

    lines = [
        "CRM MIGRATION INTEGRITY REPORT",
        "=" * 40,
        f"Source rows read........ {result.source_rows}",
        f"  -> Loaded to target... {len(result.loaded)}",
        f"  -> Suppressed......... {len(result.suppressed)}",
        f"  -> Duplicates dropped. {len(result.duplicates)}",
        f"  -> Invalid (no email). {len(result.invalid)}",
        "-" * 40,
        f"Reconciliation.......... {accounted} / {result.source_rows} "
        f"[{'BALANCED' if balanced else 'MISMATCH'}]",
        "",
        "Loaded contacts by consent status:",
    ]
    for status, count in sorted(consent_breakdown.items()):
        lines.append(f"  {status:<14} {count}")
    lines += [
        "",
        f"Mailable on target...... {mailable}",
        f"Missing provenance...... {missing_provenance}",
    ]
    if not balanced:
        lines.append("")
        lines.append("WARNING: row count does not balance. Do not import until resolved.")
    return "\n".join(lines)
