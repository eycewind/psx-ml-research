# Manual-live + ntfy adapter for accepted C11 CP7

This bundle **does not change C11**. It wraps the accepted functions in
`psx_ml.c11.live_orders`.

## Important production boundary

CP7 itself explicitly does not define how a new 2026 P4/P5 selection is
produced. Therefore this adapter requires an externally generated **live P4/P5
selection table** with the same frozen schema accepted by C11.

Do not point the runner at the historical C11 deployment-selection artifact and
pretend it is current production data.

## Files

- `src/psx_ml/live/account_state.py` — manual cash/position provider
- `src/psx_ml/live/ntfy_notifier.py` — ntfy transport
- `src/psx_ml/live/render.py` — compact human-readable notifications
- `src/psx_ml/live/manual_deployment.py` — two-phase CLI
- `config/live_account.example.json` — example state, copy to ignored live file
- `tests/live/test_manual_live.py`

## Manual account state

Copy:

```bash
cp config/live_account.example.json config/live_account.json
```

Keep `config/live_account.json` out of Git. It represents operational broker
state until StockIntel can provide cash/positions through an API.

Production C17 Phase B requires:

```json
{
  "cash_pkr": 23688,
  "deployable_capital_pkr": 50000,
  "positions": {
    "MARI": 9
  }
}
```

The deployable capital is the explicit strategy mandate used for target share
sizing. It is not inferred from brokerage NAV.

## ntfy

```bash
export NTFY_URL='https://ntfy.example.com'
export NTFY_TOPIC='psx-trades'
export NTFY_TOKEN='...optional...'
```

### Phase A — after close

```bash
python -m psx_ml.live.manual_deployment signal \
  --selections /path/to/LIVE_p4_p5_selections.parquet \
  --closes /path/to/LIVE_daily_closes.parquet \
  --signal-date 2026-08-10 \
  --notify
```

This generates target weights and frozen +2% buy limits. Exact share sizing is
intentionally deferred because accepted CP7 uses the next session's actual open.

### Phase B — next session open

Prepare a CSV/parquet with:

```text
trade_date,symbol,open_adj
```

Then:

```bash
python -m psx_ml.live.manual_deployment open \
  --plan artifacts/live/latest_signal_plan.parquet \
  --opens /path/to/session_opens.csv \
  --execution-date 2026-08-11 \
  --account-state config/live_account.json \
  --notify
```

This calls the accepted CP7 `build_session_open_orders(...)` function and emits
whole-share SELL/BUY/HOLD tickets with exact accepted fee rules and +2% no-chase
BUY logic.

## Still required before genuine live deployment

A production adapter that builds the **new 2026 P4 and P5 selections** from the
frozen accepted ranking/screening methodology. That source was not included in
the CP7 bundle and must be wired separately rather than invented here.
