# C17 - Daily Production Orchestration Contract

## Status

Implemented for branch `c17-daily-production-orchestration`.

## System Inputs Read

The ML implementation follows the system-owned C17 files in
`/media/ata/Data/personal/psx/psx-system`:

- `MASTER-CONTRACTS/C17-MASTER-CONTRACT.md`
- `interfaces/C17/PHASE-A-DECISION.md`
- `interfaces/C17/LIVE-OPEN.md`
- `acceptance/C17/ACCEPTANCE.md`

Those files are read-only to this repository.

## Frozen Baseline

C17 preserves accepted C16 behavior:

- allocation: `A07_P4_25_P5_75`;
- accepted P4/P5 selection behavior;
- frozen production model and model hash;
- accepted scoring and feature methodology;
- accepted C11/C16 signal-plan and order-ticket construction;
- canonical watcher JSON ticket schema.

C17 does not retrain, optimize, add broker execution, add StockIntel, modify
watcher, or modify `psx-system`.

## ML Scope

### Phase A - After Close

Input:

- exact `signal_date`;
- explicit intended `execution_date`;
- authoritative `daily_ohlc` through `signal_date`;
- accepted frozen scorer/model/config/reference data.

Phase A must not require execution-session open data.

Output:

- `artifacts/live/<signal-date>/features.parquet`;
- `artifacts/live/<signal-date>/predictions.parquet`;
- `artifacts/live/<signal-date>/selections.parquet`;
- `artifacts/live/<signal-date>/signal_plan.parquet`;
- `artifacts/live/<signal-date>/selection_manifest.json`;
- `artifacts/live/<signal-date>/phase_a_decision_manifest.json`.

The Phase-A manifest records allocation, dates, model identity/hash, code
revision, source data identity/hash, output hashes, and stable
`phase_a_decision_sha256`.

For an existing allocation/signal/execution identity, a materially different
decision must fail explicitly rather than silently overwrite the accepted
decision.

### Phase B - Execution Session

Input:

- frozen Phase-A manifest;
- C17 `LIVE-OPEN` artifact;
- manual account-state file.

The manual account-state schema is:

```json
{
  "cash_pkr": 23688,
  "deployable_capital_pkr": 50000,
  "positions": {
    "MARI": 9
  }
}
```

`cash_pkr` and `positions` are factual broker state. `deployable_capital_pkr` is
the explicit strategy capital mandate and must not be inferred from broker NAV
in production Phase B.

Phase B must not rescore or regenerate selections.

The C17 live-open logical schema is:

```text
trade_date
symbol
open
first_qualifying_poll_ts
confirmed_poll_ts
confirmation_count
source
```

Validation:

- `trade_date` must equal intended `execution_date`;
- `source` must be `psx_portal`;
- `open` must be finite and positive;
- timestamps must be at or after `09:40:00 Asia/Karachi`;
- `confirmation_count >= 2`;
- all target/current-position symbols required by accepted order construction
  must have valid opens.

Phase B maps raw live `open` to the accepted `build_session_open_orders(...)`
execution reference input without changing business semantics.

Target sizing is:

```text
target_value(symbol) = deployable_capital_pkr * target_weight
target_shares = floor(target_value(symbol) / execution_open_price)
```

Actual broker cash remains the affordability constraint for BUY orders after
SELL proceeds and fees. If the requested BUY delta cannot be afforded, existing
cash clipping/skip behavior applies without changing desired target shares.

Output:

- retained Parquet ticket:
  `artifacts/live/<signal-date>/order_ticket_<execution-date>.parquet`;
- watcher-facing JSON ticket:
  `artifacts/live/<signal-date>/order_ticket_<execution-date>.json`;
- production manifest:
  `artifacts/live/<signal-date>/production_manifest.json`.

The JSON ticket is a non-empty top-level array of order-row objects. It is not
wrapped in an envelope. `signal_date` and `execution_date` serialize as ISO
`YYYY-MM-DD` strings.

The Phase-B manifest traces back to the frozen Phase-A manifest path/hash and
`phase_a_decision_sha256`.

For an existing allocation/signal/execution identity, a materially different
ticket must fail explicitly rather than silently overwrite the accepted ticket.

## Acceptance Coverage

ML-owned SYS-AT coverage:

- SYS-AT05: Phase A requires no execution-session open.
- SYS-AT06: Phase A deterministically emits a frozen decision artifact.
- SYS-AT07: Phase A preserves accepted P4/P5/allocation policy.
- SYS-AT11: Phase B consumes frozen Phase A without recomputing signals.
- SYS-AT12: Phase B emits canonical watcher JSON directly.
- SYS-AT20: C16/C10/C11 accepted regression suites remain passing.
- SYS-AT21: no StockIntel/broker/order-submission capability introduced.
- SYS-AT22: A07 strategy/model/allocation remains frozen.

Regression fixture:

```text
signal_date: 2026-08-13
execution_date: 2026-08-17
```

This pair remains valid and explicit; the implementation does not infer
execution date from the next calendar weekday.
