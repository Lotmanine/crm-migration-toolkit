# crm-migration-toolkit

A small, **dependency-free** (Python standard library only) pipeline for migrating contacts between CRM/ESP platforms the way a real migration should be done: every source row is accounted for, consent and its provenance survive the move, and the result is **reconciled** before anyone imports it.

Built as a reusable tool and shipped with synthetic sample data so it runs end to end out of the box. This is the pattern I use on client migrations (Mailchimp / ActiveCampaign / Klaviyo / Keap / HubSpot → FluentCRM and others); the client data is never in the repo.

## The idea

```
source export ──▶ extract ──▶ transform ──▶ suppress ──▶ dedupe ──▶ target import
                                                  │
                                                  ▼
                                      integrity report (reconciled)
```

Everything maps through one **canonical contact model** ([`crm_migrate/models.py`](crm_migrate/models.py)). Source columns and target fields never line up, so the mapping is **data, not code** ([`samples/mapping.json`](samples/mapping.json)) - point it at a different pair of platforms by swapping the config.

## What it actually handles

- **Consent normalization** across platforms' different vocabularies (`active`/`confirmed` → `subscribed`, `bounced`/`invalid` → `cleaned`, unknown → `pending` so nobody is silently made mailable).
- **Consent provenance** - synthesizes an audit string (where + when + which system) for every contact. The field most migrations lose, and the one the receiving ESP and regulators care about.
- **Suppression merge** - applies a suppression list with the *same* email normalization used on extract, so suppressed contacts can't slip through on a casing difference.
- **Case-insensitive dedupe** - `Alice@Example.com` and `alice@example.com` are one person.
- **Reconciliation** - `source_rows == loaded + suppressed + duplicates + invalid`. If it doesn't balance, the report says **MISMATCH** and tells you not to import.

## Run it

```bash
python -m crm_migrate \
  --source samples/mailchimp_export.csv \
  --mapping samples/mapping.json \
  --suppression samples/suppression.csv \
  --out build/fluentcrm_import.csv
```

Output on the sample data:

```
CRM MIGRATION INTEGRITY REPORT
========================================
Source rows read........ 12
  -> Loaded to target... 8
  -> Suppressed......... 2
  -> Duplicates dropped. 1
  -> Invalid (no email). 1
----------------------------------------
Reconciliation.......... 12 / 12 [BALANCED]

Loaded contacts by consent status:
  cleaned        1
  pending        1
  subscribed     4
  unsubscribed   2

Mailable on target...... 4
Missing provenance...... 0
```

## Tests

```bash
python -m unittest discover -s tests -t .
```

9 tests covering normalization, dedupe, suppression, provenance, and reconciliation.

## Adapting to your platforms

- **Different source?** Edit `samples/mapping.json` to match its export columns.
- **Different target?** `write_target_csv()` in [`crm_migrate/pipeline.py`](crm_migrate/pipeline.py) emits a FluentCRM-shaped CSV; change the header list / row builder for Klaviyo, ActiveCampaign, etc.

## Author

Built by **Lotfi Otmanine**, senior WordPress developer at [OLDEV](https://oldev.site).

- Website: [oldev.site](https://oldev.site)
- Hire me on Upwork: [upwork.com/freelancers/~01bd748fcb665b90ca](https://www.upwork.com/freelancers/~01bd748fcb665b90ca)
- LinkedIn: [linkedin.com/in/lotfi-otmanine](https://www.linkedin.com/in/lotfi-otmanine)
- GitHub: [github.com/Lotmanine](https://github.com/Lotmanine)

## License

MIT.
