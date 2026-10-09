# CSV Quality Audit

**Catch common data problems before they reach a dashboard.**

A local CSV validation tool with explicit JSON rules, deterministic reports and automation-friendly exit codes. The source file is never modified.

## Quick start

Python 3.10+; no third-party dependencies. Run from the repository root:

```bash
python audit.py data/clean.csv --contract contract.json
python audit.py data/dirty.csv --contract contract.json --out reports/dirty-report.json
python -m unittest discover -v
```

The clean example exits **0**. The deliberately dirty example exits **1**, finding one duplicate row, one duplicated customer ID, one missing region, two invalid numeric values, and one malformed record. Malformed records are excluded from per-column checks. Example JSON reports are included under `examples/`.

## Rules

```json
{"required": ["customer_id", "region", "order_total"], "unique": ["customer_id"], "numeric": ["order_total"]}
```

- `required`: blank values fail.
- `unique`: each nonblank value must occur once in that column.
- `numeric`: nonblank values must parse as a finite decimal. `NaN` and infinity fail.
- Duplicate complete rows and incorrect field counts fail automatically.
- A header-only dataset fails. Missing or duplicate headers and invalid contracts are input errors.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Dataset passes all configured checks |
| 1 | Report generated; data-quality issues found |
| 2 | Input, contract, parsing or file error |

Values are whitespace-trimmed for comparisons; case is preserved. Unique rules apply per column, not as a composite key. Optional numeric blanks are allowed unless that field is also required. Record numbers count CSV records (header = 1), not physical lines inside quoted multiline fields. Reports contain counts and column names, not row values.

## Boundaries

UTF-8 comma-separated files only. Literal `NULL` and `N/A` are treated as text, not missing values. Unique values and whole rows are held in memory, so this version is for small and medium datasets. It does not check email validity, dates, ranges, cross-table relationships or personally identifiable information.

## Why it belongs in an analytics workflow

Use this as an explicit validation step before SQL imports, Excel reports or Power BI refreshes. The included synthetic fixtures and tests make the pass/fail behavior reproducible.
