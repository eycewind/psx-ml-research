# C17 Daily Production Orchestration

Use the project conda environment:

```bash
conda activate psx-ml-research
```

CLI entry point:

```bash
psx-live-production-ticket <command> ...
```

## Phase A - After Close

Phase A freezes the signal decision. It does not require execution-session open
data or account state.

```bash
psx-live-production-ticket phase-a \
  --source-db /path/to/psx_watcher.db \
  --signal-date 2026-08-13 \
  --execution-date 2026-08-17 \
  --repo /media/ata/Data/personal/psx/psx-ml-research
```

Output:

```text
artifacts/live/2026-08-13/phase_a_decision_manifest.json
artifacts/live/2026-08-13/selections.parquet
artifacts/live/2026-08-13/signal_plan.parquet
```

## Phase B - Execution Session

Phase B consumes the frozen Phase-A decision, a watcher-produced settled
live-open artifact, and manual account state. It does not rescore or regenerate
selections.

```bash
psx-live-production-ticket phase-b \
  --phase-a-manifest artifacts/live/2026-08-13/phase_a_decision_manifest.json \
  --live-open /path/to/settled_live_open.json \
  --account-state config/live_account.json
```

The live-open file may be CSV, Parquet, or JSON top-level row array with:

```text
trade_date,symbol,open,first_qualifying_poll_ts,confirmed_poll_ts,confirmation_count,source
```

The `open` field is the raw live PSX portal execution open. Source must be
`psx_portal`, timestamps must be at or after `09:40:00 Asia/Karachi`, and
`confirmation_count` must be at least 2.

Output:

```text
artifacts/live/2026-08-13/order_ticket_2026-08-17.parquet
artifacts/live/2026-08-13/order_ticket_2026-08-17.json
artifacts/live/2026-08-13/production_manifest.json
```

The watcher-facing JSON is a non-empty top-level list of order-row objects.

## Compatibility Wrapper

The `run` command retains the C16-style one-shot path for compatibility tests:

```bash
psx-live-production-ticket run \
  --source-db /path/to/psx_watcher.db \
  --signal-date 2026-08-13 \
  --execution-date 2026-08-17 \
  --account-state config/live_account.json
```
