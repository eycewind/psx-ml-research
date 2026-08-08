# C11 CP1 — Deployment Freeze Report

- Branch: `feature/c11-deployment-policy`
- HEAD: `612db3c1636d73e745def8a8c732c20279ac1f5b`
- Accepted C10 tag: `c10-fee-aware-portfolio-accepted`
- Holdout accessed: `false`

## Frozen upstream policies

- `P1_broad_canonical`
- `P2_conservative_consensus`
- `P4_kmi30_strict`
- `P5_shariah_screened`

## Mandatory deployment Shariah gate

- Every executable BUY candidate must pass PIT Shariah eligibility.
- Ineligible candidates are rejected.
- Unknown/unavailable eligibility is rejected.
- Low-confidence eligible candidates are allowed but explicitly flagged.
- Sector names are not used as a proxy for Shariah eligibility.
- P1/P2 remain immutable research policies; C11 will derive gated deployment variants.

## Frozen inputs

| Artifact | Rows | Date range | Policies / confidence | SHA-256 |
|---|---:|---|---|---|
| `data/processed/c9/candidate_selections.parquet` | 5730 | 2023-01-02 to 2025-12-30 | P1_broad_canonical, P2_conservative_consensus, P3_high_conviction | `3ff902152a75d168218850535d4c40da4dd949b54e22ccdfc6560d39646dc520` |
| `data/processed/c10/p4_kmi30_selections.parquet` | 471 | 2023-01-02 to 2025-12-29 | P4_kmi30_strict | `75ef50328110d573649906d47ee08733b60977953bb7c67c37d869eae05fd03c` |
| `data/processed/c10/p5_shariah_screened_selections.parquet` | 1550 | 2023-01-02 to 2025-12-29 | P5_shariah_screened | `0166c4a67c6d12241ddef1b7f7fc4002d6fa8071d01cbd6499b32dd22811c57c` |
| `data/reference/kmi_all_share_screened_universe_history.csv` | 2440 | 2022-01-03 to 2025-12-02 | confidence=high,low,medium | `525bb1e26e4b9ec71b838122b27e63ce1c95755f4b244991973f6d2da949f70a` |

## CP2 capital grid

PKR 50,000; 100,000; 250,000; 500,000; 1,000,000.

## Boundaries

- No model retraining or signal redesign.
- No C8/C9/C10 accepted artifact mutation.
- No 2026 holdout use for policy design or tuning.
- C11 deployment transformations must remain traceable to their upstream policy.

## Result

CP1 input freeze and deployment-gate specification: **PASS**.
