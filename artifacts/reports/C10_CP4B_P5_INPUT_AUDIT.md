# C10 CP4B — P5 Input Audit

This audit identifies the exact accepted prediction, feature/liquidity, sector, and date sources required before generating P5 selections.

## P1 weekly date source

- Missing `data/processed/c9/candidate_selections.parquet`.

## Screened-universe artifact

- Rows: 2440
- Intervals: 9
- Confidence values: high, low, medium

## Candidate data tables

| Path | Rows | Relevant columns |
|---|---:|---|
| `data/reference/kmi30_membership_history.csv` | 180 | symbol |
| `data/reference/kmi_all_share_baseline_2022_01_03.csv` | 250 | symbol |
| `data/reference/kmi_all_share_baseline_2022_01_03.parquet` | 250 | symbol |
| `data/reference/kmi_all_share_screened_universe_history.csv` | 2440 | symbol |
| `data/reference/kmi_all_share_screened_universe_history.parquet` | 2440 | symbol |
| `data/reference/psx_security_master_2026-08-01.parquet` | 1387 | symbol, sector |

## Stop condition

Do not implement the P5 generator until the exact accepted C8 OOF prediction table, PIT liquidity table, sector source, and P1 weekly dates have been identified.
