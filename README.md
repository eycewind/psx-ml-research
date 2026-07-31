# psx-ml-research

Leakage-safe machine-learning research foundation for Pakistan Stock Exchange
daily data. C1 only audits and extracts source data; it does not implement
features, targets, models, or backtests.

The production watcher database is always opened with SQLite URI `mode=ro` and
`PRAGMA query_only=ON`. All generated files belong under this repository.

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/psx-c1 run --source-db /home/hassan/psx-stock-watcher/data/psx_watcher.db
.venv/bin/pytest
```

See [the C1 contract](contracts/C1_DATA_FOUNDATION_AND_AUDIT/CONTRACT.md) and
the generated report under `artifacts/reports/`.
