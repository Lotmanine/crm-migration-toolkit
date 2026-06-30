"""Field mapping.

A migration is mostly a mapping problem: the source's column names and the
target's field keys never line up, custom fields get renamed, and consent
provenance has to be synthesized from several columns. The mapping is data
(JSON), not code, so the same toolkit migrates any pair of platforms by
swapping the config file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class Mapping:
    """Loaded from a mapping.json. See samples/mapping.json for the format."""

    # source column name -> canonical Contact attribute
    standard: dict[str, str]
    # source column name -> custom field key on the canonical model
    custom: dict[str, str]
    # source column holding the tag list, plus its delimiter
    tags_column: str
    tags_delimiter: str
    # how to build the consent_provenance audit string
    consent_status_column: str
    consent_date_column: str
    source_system: str

    @classmethod
    def from_file(cls, path: str) -> "Mapping":
        with open(path, encoding="utf-8") as fh:
            raw: dict[str, Any] = json.load(fh)
        return cls(
            standard=raw.get("standard", {}),
            custom=raw.get("custom", {}),
            tags_column=raw.get("tags_column", ""),
            tags_delimiter=raw.get("tags_delimiter", ","),
            consent_status_column=raw.get("consent_status_column", ""),
            consent_date_column=raw.get("consent_date_column", ""),
            source_system=raw.get("source_system", "unknown"),
        )
