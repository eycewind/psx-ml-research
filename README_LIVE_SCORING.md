# Live scorer

Frozen inference adapter for the accepted direct-rank LightGBM model.

Model: `rank_5_B_market_context_fold_2025_lightgbm_cpu.txt`

SHA-256: `ecc95b9d78aa4dd26b30dbe4560eec716d4f21a8e190e59ea02b84a75d3643d5`

No retraining is performed.

## Test

```bash
python -m pytest -q tests/live
```

## Historical parity gate

```bash
python -m psx_ml.live.live_scoring parity \
  --source-db /media/ata/Data/personal/psx/stock-watcher/data/psx_watcher.db \
  --date 2025-12-22
```

## Live score

```bash
python -m psx_ml.live.live_scoring score \
  --source-db /media/ata/Data/personal/psx/stock-watcher/data/psx_watcher.db \
  --date 2026-08-10
```

Outputs go to `artifacts/live/<date>/` and never overwrite frozen research artifacts.
