# C16 - Production Ticket Pipeline Delivery

## Implementation Summary

Implemented a production-safe A07 orchestration adapter in
`psx_ml.live.production_pipeline`.

The adapter:

- requires explicit `signal_date` and `execution_date`;
- validates exact required production dates in `daily_ohlc`;
- fails closed on missing schema, missing date rows, duplicate price rows, and
  invalid close/open prices;
- calls the accepted frozen live scorer;
- requires exact signal-date prediction and feature rows after scoring;
- builds current P4/P5 selections through the accepted live selection adapter,
  which reuses C10 P4/P5 mechanics;
- builds the signal plan through accepted C11 `build_signal_plan`;
- builds the order ticket through accepted C11 `build_session_open_orders`;
- preserves the existing Parquet ticket at
  `order_ticket_<execution-date>.parquet`;
- emits the watcher-facing handoff artifact at
  `order_ticket_<execution-date>.json`;
- serializes the watcher-facing JSON as a top-level array of the exact order
  business rows, with `signal_date` and `execution_date` as ISO `YYYY-MM-DD`
  strings;
- preserves allocation `A07_P4_25_P5_75`;
- writes canonical live artifacts under `artifacts/live/<signal-date>/`;
- writes `production_manifest.json` with code revision, dates, allocation,
  source DB identity, account-state hash, feature/prediction hashes, selection
  hash, signal-plan hash, Parquet order-ticket hash, JSON order-ticket hash,
  JSON top-level type, scoring manifest, selection manifest, and emitted
  order-ticket schema.

No strategy research, model retraining, parameter optimization, broker API
execution, or order-ticket schema redesign was performed.

## Files Changed

- `contracts/C16-CONTRACT.md`
- `contracts/C16-DELIVERY.md`
- `pyproject.toml`
- `src/psx_ml/live/production_pipeline.py`
- `tests/live/test_production_pipeline.py`

## Preserved ML Order-Ticket Schema

The production adapter preserves the existing ML order-ticket schema emitted by
`build_session_open_orders`:

```text
allocation_id
signal_date
execution_date
symbol
target_weight
current_shares
target_shares
order_side
order_shares
order_type
reference_open
buy_limit_price
status
reason
estimated_notional
estimated_commission
estimated_sst
estimated_cdc
estimated_total_cost
cash_after_planned_orders
```

## Watcher Handoff Correction

System acceptance identified that stock-watcher imports only a top-level
non-empty JSON array of order-row objects. C16 now keeps the existing ML Parquet
artifact and additionally emits:

```text
artifacts/live/<signal-date>/order_ticket_<execution-date>.json
```

The JSON handoff is not wrapped in an object. It represents the same business
rows as the Parquet ticket and is included in `production_manifest.json` with
path, SHA-256, row count, and `top_level_type = list`.

No `psx-system` or stock-watcher files were changed.

## Commands and Results

Focused C16-relevant test suite:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_PYTHON_INSTALL_DIR=/tmp/uv-python uv run --python 3.11 --extra dev --extra trees pytest -q tests/live tests/c10/test_p4_selection.py tests/c10/test_p5_selection.py tests/c10/test_p4_c10_integration.py tests/c10/test_p5_c10_integration.py tests/c11/test_live_orders.py tests/c11/test_capital_allocation.py
```

Result:

```text
..................................                                       [100%]
```

The focused suite includes
`test_json_ticket_is_top_level_list_and_matches_parquet_business_rows`, which
loads `order_ticket_2026-08-11.json`, proves the JSON top-level type is `list`,
proves it is non-empty, proves dates are serialized as `2026-08-10` and
`2026-08-11`, and proves JSON rows equal the normalized Parquet business rows.

Compile check:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_PYTHON_INSTALL_DIR=/tmp/uv-python uv run --python 3.11 python -m py_compile src/psx_ml/live/production_pipeline.py tests/live/test_production_pipeline.py
```

Result:

```text
passed with no output
```

Full suite attempted:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_PYTHON_INSTALL_DIR=/tmp/uv-python uv run --python 3.11 --extra dev --extra trees pytest -q
```

Result:

```text
blocked during collection by missing optional/pre-existing dependencies:
ModuleNotFoundError: No module named 'pdfplumber'
ModuleNotFoundError: No module named 'torch'
```

## Limitations / Blockers

- Full repository test collection requires optional dependencies not declared in
  the selected extras used here (`pdfplumber`, `torch`). The C16-relevant live,
  C10 P4/P5, and C11 order/allocation suites passed.
- The adapter still uses the existing manual account-state file for cash and
  positions. It does not add broker API execution.
- Stock-watcher importer execution was not run in this repository. The
  watcher-facing artifact shape was implemented from the system architect's
  frozen interface decision.

## Final Commit Hash

Initial C16 implementation:

`5e00fdddb8a53d6614a6402dec53068ebdb1a611`

JSON handoff follow-up:

Created after this delivery document update; exact commit hash is reported in
the final C16 follow-up response.
