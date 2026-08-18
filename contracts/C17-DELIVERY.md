# C17 - Daily Production Orchestration Delivery

## Implementation Summary

Implemented the ML-owned C17 two-phase production workflow in
`psx_ml.live.production_pipeline`.

Phase A:

- accepts explicit `signal_date` and intended `execution_date`;
- validates signal-date `daily_ohlc.close_adj`;
- does not require execution-session open data;
- reuses the accepted frozen live scorer;
- reuses accepted P4/P5 live selection construction;
- reuses accepted C11 `build_signal_plan`;
- persists durable Phase-A artifacts and
  `phase_a_decision_manifest.json`;
- records model identity/hash, code revision, source/input/output hashes,
  allocation, dates, selections, signal plan, and stable
  `phase_a_decision_sha256`;
- fails explicitly on conflicting same allocation/signal/execution decisions.

Phase B:

- consumes the frozen Phase-A manifest;
- consumes a watcher-produced C17 LIVE-OPEN file;
- does not rescore or regenerate selections;
- validates exact execution date, `source=psx_portal`, finite positive raw
  live `open`, timestamps at/after `09:40:00 Asia/Karachi`,
  `confirmation_count >= 2`, and all required symbols;
- maps raw live `open` into the accepted `build_session_open_orders(...)`
  input shape without changing business semantics;
- emits retained Parquet and canonical watcher JSON tickets;
- records Phase-B provenance back to Phase-A manifest hash and
  `phase_a_decision_sha256`;
- fails explicitly on conflicting same allocation/signal/execution tickets.

The C16-compatible `run` command remains available for regression coverage.

## Files Changed

- `README_C17_DAILY_PRODUCTION.md`
- `contracts/C17-CONTRACT.md`
- `contracts/C17-DELIVERY.md`
- `src/psx_ml/live/production_pipeline.py`
- `tests/live/test_production_pipeline.py`

## CLI

```bash
psx-live-production-ticket phase-a ...
psx-live-production-ticket phase-b ...
psx-live-production-ticket run ...
```

See `README_C17_DAILY_PRODUCTION.md`.

## Test Evidence

Environment:

```text
/home/ata/miniconda3/envs/psx-ml-research/bin/python
Python 3.12.12
```

Live/compile check:

```bash
python -m py_compile src/psx_ml/live/production_pipeline.py tests/live/test_production_pipeline.py
pytest -q tests/live
```

Result:

```text
..................                                                       [100%]
```

C17-relevant plus accepted C16 regression suite:

```bash
pytest -q tests/live tests/c10/test_p4_selection.py tests/c10/test_p5_selection.py tests/c10/test_p4_c10_integration.py tests/c10/test_p5_c10_integration.py tests/c11/test_live_orders.py tests/c11/test_capital_allocation.py
```

Result:

```text
.......................................                                  [100%]
```

## Coverage Notes

Automated tests cover:

- Phase A does not require execution-session open data;
- deterministic Phase-A decision;
- conflicting Phase-A decision fails explicitly;
- exact signal/execution date validation;
- stale/missing signal-date input fails closed through existing C16 tests;
- Phase B consumes frozen Phase A and has no scorer/regeneration path;
- wrong-date live-open artifact fails;
- missing required symbol open fails;
- canonical watcher JSON is a top-level non-empty list;
- JSON reconciles to Parquet business rows;
- Phase-B provenance links to Phase-A hash;
- accepted allocation/model/policy remain unchanged;
- `2026-08-13 -> 2026-08-17` holiday/weekend pair remains valid.

## Known Full-Suite Limitation

The full historical repository suite is known to fail collection in the
intended conda environment because `torch` is absent. Per C17 instruction,
`torch` was not installed merely to close this contract.

## Interface Blockers

No ML-owned C17 interface blocker was found.

No `psx-system`, stock-watcher, strategy, allocation, model, broker, or
StockIntel changes were made.

## Final Commit Hash

The exact C17 implementation commit hash is reported in the final response
after this delivery document is committed.
