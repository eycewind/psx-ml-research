# C16 - Production Ticket Pipeline Contract

## Status

Draft implementation contract for branch `c16-production-ticket-pipeline`.

Immutable baseline:

```text
e549e6c462e922c260e8865c0b4c5d666750070b
tag: pre-c16-ml-baseline
```

## Scope

C16 closes the ML repository production path:

```text
current production data
  -> current P4/P5 selections
  -> accepted signal-plan construction
  -> accepted order-ticket construction
  -> stock-watcher handoff artifact
```

C16 must reuse the accepted frozen methodology and deployment mechanics. It must
not retrain models, optimize parameters, redefine the order-ticket schema, add
broker execution, or modify `psx-system` / `psx-stock-watcher`.

## Frozen Decisions

- Strategy/model/policy: accepted A07 remains frozen.
- Allocation: `A07_P4_25_P5_75`.
- P4 policy source: accepted C10 KMI-30 strict selection mechanics.
- P5 policy source: accepted C10 Shariah-screened selection mechanics.
- Live scoring source: accepted frozen LightGBM live-scoring adapter and C8
  feature order.
- Signal/order construction: accepted C11 CP7 `build_signal_plan` and
  `build_session_open_orders`.

## Requirement Map

Because the cross-repository MASTER CONTRACT is not present in this repository,
this file records the ML-side C16 requirement labels used for this component.

| ID | ML repository obligation |
|---|---|
| ML-R1 | Provide a deterministic production path from current market data to current P4/P5 selections using frozen accepted methodology. |
| ML-R2 | Reuse accepted live scoring/model loading and feature construction; do not retrain or optimize. |
| ML-R3 | Reuse accepted C10 P4/P5 selection mechanics and accepted C11 signal/open order builders. |
| ML-R4 | Preserve allocation `A07_P4_25_P5_75` and existing ML order-ticket schema. |
| ML-R5 | Fail closed on missing, stale, wrong-date, inconsistent, or manually substituted required production inputs. |
| ML-R6 | Write production artifacts under canonical `artifacts/live/<signal-date>/` layout with sufficient provenance, including both retained Parquet ticket and watcher-facing JSON handoff hashes. |
| ML-R7 | Support explicit dates and reproducible deterministic reruns. |
| ML-R8 | Add automated tests for selection determinism, JSON handoff determinism/reconciliation, no manual selection-file dependency, fail-closed input handling, allocation/schema preservation, and existing accepted live behavior. |

## Applicable SYS-AT Trace

The following SYS-AT labels are the ML-side interpretation of the system
acceptance requirements supplied for C16.

| SYS-AT | Coverage in this repo |
|---|---|
| SYS-AT-C16-1 | Production pipeline can generate current P4/P5 selections from current production data, then build signal plan and order ticket. |
| SYS-AT-C16-2 | Production path does not require an externally/manual generated live selection file. |
| SYS-AT-C16-3 | Production mode fails closed for missing required input. |
| SYS-AT-C16-4 | Production mode fails closed for stale or wrong-date required input. |
| SYS-AT-C16-5 | Accepted allocation remains `A07_P4_25_P5_75`. |
| SYS-AT-C16-6 | Existing signal-plan and order-ticket constructors remain the production constructors. |
| SYS-AT-C16-7 | Production artifacts include provenance for code revision, dates, allocation, inputs, selections, signal plan, ticket, and hashes. |
| SYS-AT-C16-8 | Watcher-facing ticket handoff is `order_ticket_<execution-date>.json`, a top-level non-empty JSON array of the same business rows emitted by `build_session_open_orders`. |

## Interface Boundary

C16 preserves the ML Parquet order-ticket artifact and emits an additional
watcher-facing JSON handoff artifact:

```text
artifacts/live/<signal-date>/order_ticket_<execution-date>.parquet
artifacts/live/<signal-date>/order_ticket_<execution-date>.json
```

The JSON document must be a top-level non-empty array of order-row objects:

```json
[
  {
    "allocation_id": "A07_P4_25_P5_75"
  }
]
```

It must not be wrapped as `{"orders": [...]}`. JSON rows must represent the
exact business rows returned by the accepted `build_session_open_orders(...)`
constructor. `signal_date` and `execution_date` must serialize as ISO
`YYYY-MM-DD` strings. This serialization correction must not alter strategy,
policy, allocation, order construction, or business values.

## Planned Implementation

Add a small production orchestration adapter that:

1. Validates explicit signal and execution dates.
2. Scores the frozen live model for the signal date.
3. Generates current P4/P5 selections with `psx_ml.live.live_selection`.
4. Builds the accepted C11 signal plan.
5. Builds the accepted C11 session-open order ticket.
6. Writes retained Parquet and watcher-facing JSON order-ticket artifacts.
7. Writes date-partitioned live artifacts and a final manifest containing
   hashes and provenance.

The adapter may add validation around existing functions, but it must not fork
policy/scoring/order logic.

## Acceptance Tests

Automated tests must cover:

- deterministic production selection;
- no manual selection file required for production path;
- missing required input fails closed;
- stale/wrong-date required input fails closed;
- accepted allocation remains unchanged;
- existing signal-plan construction still works;
- existing order-ticket construction still works;
- watcher-facing JSON is a top-level list;
- watcher-facing JSON business rows reconcile with the retained Parquet ticket;
- no regression of existing accepted live tests.

## Out of Scope

- Broker API execution.
- New strategy research.
- Parameter optimization.
- Model retraining.
- Cross-repository interface redefinition.
- Silent fallback to older market data.
