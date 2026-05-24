# Citevault Golden Set

Fictional, synthetic test cases for the Citevault eval framework. GDPR-safe by
construction. Used by `citevault eval --golden ./golden/`.

Each case has:
- `evidence/` — candidate's source materials
- `job_posting.txt` — the role to tailor for
- `expectations.yaml` — per-requirement expected outcomes
- `reference_output/` — optional human-curated ideal output (empty in v1)

See [Architecture doc](../docs/architecture.md) for the eval framework overview.
