"""End-to-end tests over the synthetic sample data.

Run with:  python -m pytest   (or: python -m unittest)
"""

import os
import unittest

from crm_migrate.integrity import build_report
from crm_migrate.mapping import Mapping
from crm_migrate.normalize import normalize_consent, normalize_email, normalize_phone
from crm_migrate.pipeline import run

HERE = os.path.dirname(__file__)
SAMPLES = os.path.join(HERE, "..", "samples")


class TestNormalize(unittest.TestCase):
    def test_email_lowercased_and_trimmed(self):
        self.assertEqual(normalize_email("  Alice@Example.COM "), "alice@example.com")

    def test_invalid_email_returns_empty(self):
        self.assertEqual(normalize_email("notanemail"), "")

    def test_phone_keeps_plus_and_digits(self):
        self.assertEqual(normalize_phone("+1 (415) 555-0100"), "+14155550100")
        self.assertEqual(normalize_phone("415-555-0142"), "4155550142")

    def test_consent_aliases(self):
        self.assertEqual(normalize_consent("active"), "subscribed")
        self.assertEqual(normalize_consent("bounced"), "cleaned")
        self.assertEqual(normalize_consent("who knows"), "pending")


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.mapping = Mapping.from_file(os.path.join(SAMPLES, "mapping.json"))
        self.result = run(
            os.path.join(SAMPLES, "mailchimp_export.csv"),
            self.mapping,
            os.path.join(SAMPLES, "suppression.csv"),
        )

    def test_reconciliation_balances(self):
        accounted = (
            len(self.result.loaded)
            + len(self.result.suppressed)
            + len(self.result.invalid)
            + len(self.result.duplicates)
        )
        self.assertEqual(accounted, self.result.source_rows)

    def test_expected_buckets(self):
        self.assertEqual(self.result.source_rows, 12)
        self.assertEqual(len(self.result.loaded), 8)
        self.assertEqual(len(self.result.suppressed), 2)
        self.assertEqual(len(self.result.duplicates), 1)
        self.assertEqual(len(self.result.invalid), 1)

    def test_case_insensitive_dedupe(self):
        emails = [c.email for c in self.result.loaded]
        self.assertEqual(len(emails), len(set(emails)))
        self.assertIn("alice@example.com", emails)

    def test_every_loaded_contact_has_provenance(self):
        self.assertTrue(all(c.consent_provenance for c in self.result.loaded))

    def test_report_marks_balanced(self):
        self.assertIn("BALANCED", build_report(self.result))


if __name__ == "__main__":
    unittest.main()
