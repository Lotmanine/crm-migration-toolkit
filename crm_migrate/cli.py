"""Command-line entry point.

    python -m crm_migrate \
        --source samples/mailchimp_export.csv \
        --mapping samples/mapping.json \
        --suppression samples/suppression.csv \
        --out build/fluentcrm_import.csv
"""

from __future__ import annotations

import argparse
import os

from .integrity import build_report
from .mapping import Mapping
from .pipeline import run, write_target_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Platform-agnostic CRM/ESP migration pipeline.")
    parser.add_argument("--source", required=True, help="source export CSV")
    parser.add_argument("--mapping", required=True, help="mapping.json")
    parser.add_argument("--suppression", help="optional suppression list CSV")
    parser.add_argument("--out", default="build/target_import.csv", help="target import CSV to write")
    parser.add_argument("--report", help="optional path to write the integrity report")
    args = parser.parse_args(argv)

    mapping = Mapping.from_file(args.mapping)
    result = run(args.source, mapping, args.suppression)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    write_target_csv(result.loaded, args.out)

    report = build_report(result)
    print(report)
    if args.report:
        os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write(report + "\n")

    print(f"\nWrote {len(result.loaded)} contacts -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
