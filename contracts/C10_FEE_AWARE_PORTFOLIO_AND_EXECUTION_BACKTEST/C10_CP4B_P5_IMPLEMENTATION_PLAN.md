# C10 CP4B — P5 Point-in-Time Shariah All-Share Policy

## Objective

Add a fifth policy:

- `P5_shariah_all_share`
- Point-in-time universe: official **PSX-KMI All Share Islamic Index**
- Same accepted C8 prediction basis used by P4:
  - model: `lightgbm_cpu`
  - horizon: `5`
  - target family: stored C8 label `market_relative`
  - feature variant: `B_market_context`
- Weekly signal dates identical to P1/P4
- Top 10% of eligible point-in-time Shariah-compliant candidates
- Maximum two selected companies per sector
- Liquidity screen: remove bottom 25% by point-in-time
  `turnover_median_20obs_adj`
- No 2026 holdout use
- No model retraining
- No changes to C8/C9 predictions
- Existing P1/P2/P4 results must remain numerically unchanged

P5 must use official company-level Shariah classification. It must not use
blanket sector exclusions. Conventional banks and conventional insurance
companies will naturally be excluded when absent from the official PSX-KMI
All Share membership; officially compliant Islamic banks, takaful operators,
Modarabas, REITs, and other compliant instruments may remain eligible.

---

## Branch and safety boundary

Create a dedicated branch after the accepted P4 work is committed:

```bash
git status --short
git switch -c feature/c10-p5-shariah-all-share
```

Do not modify:

- `psx_watcher.db`
- C8 model artifacts
- C9 prediction artifacts
- the 2026 final holdout
- existing P4 KMI-30 membership artifacts

All P5 work remains inside `psx-ml-research`.

---

# Checkpoint CP4B-1 — Build authoritative point-in-time membership

## Required source periods

The research window begins in 2023, but a complete starting membership set is
required before the first 2023 signal. Build intervals from the official PSX
notices below.

| Review period | Effective date | Official notice |
|---|---:|---|
| Jan–Jun 2021 | 2022-01-03 | `sharia_KMI_All_Share_list_June_2021_Final_27122021.pdf` |
| Jul–Dec 2021 | 2022-07-15 | `Notice-_KMI_All_Shares_Index_Recomposition_30-June-22_(M).pdf` |
| Jan–Jun 2022 | 2023-01-12 | `Copy_of_KMI_All_Share_June_-22_23122022.pdf` |
| Jul–Dec 2022 | 2023-07-10 | `Notice-666_KMI_All_Share_Index_re-composition_for_Dec-22.pdf` |
| Jan–Jun 2023 | 2023-12-26 | `Notice-_KMI-All-Index-Re-composition-Jun-30-2023-Final.pdf` |
| Jul–Dec 2023 | 2024-06-25 | `KMI-ALL-Share-Recomposition-Notice.pdf` |
| Jan–Jun 2024 | 2025-01-03 | `Notice-KMIALLshare-Notice-as-of-June-2024.pdf` |
| Jul–Dec 2024 | 2025-06-02 | `KMI-All-share-Notice-Recomposition-as-of-Dec-_2024-Final.pdf` |
| Jan–Jun 2025 | 2025-12-02 | `Merged_KMIALL_Notice_and_FinalList_June2025.pdf` |

Do not use the May 2026 recomposition in P5 research or evaluation because the
2026 final holdout remains locked.

## Official source URLs

```text
https://www.psx.com.pk/psx/themes/psx/uploads/sharia_KMI_All_Share_list_June_2021_Final_27122021.pdf
https://www.psx.com.pk/psx/themes/psx/uploads/Notice-_KMI_All_Shares_Index_Recomposition_30-June-22_%28M%29.pdf
https://www.psx.com.pk/psx/themes/psx/uploads/Copy_of_KMI_All_Share_June_-22_23122022.pdf
https://www.psx.com.pk/psx/themes/psx/uploads/Notice-666_KMI_All_Share_Index_re-composition_for_Dec-22.pdf
https://www.psx.com.pk/psx/themes/psx/uploads/Notice-_KMI-All-Index-Re-composition-Jun-30-2023-Final.pdf
https://www.psx.com.pk/psx/themes/psx/uploads/KMI-ALL-Share-Recomposition-Notice.pdf
https://www.psx.com.pk/psx/themes/psx/uploads/Notice-KMIALLshare-Notice-as-of-June-2024.pdf
https://www.psx.com.pk/psx/themes/psx/uploads/KMI-All-share-Notice-Recomposition-as-of-Dec-_2024-Final.pdf
https://www.psx.com.pk/psx/themes/psx/uploads/Merged_KMIALL_Notice_and_FinalList_June2025.pdf
```

## Important membership construction rule

Several notices provide incoming/outgoing changes rather than a clean
constituent table. Therefore:

1. Start from the complete membership list effective `2022-01-03`.
2. Apply every incoming/outgoing change in strict effective-date order.
3. Include newly listed securities on their official inclusion date only when
   the PSX notice explicitly states they join KMI All Share from listing.
4. Never infer membership from sector.
5. Never backfill a later compliant status into an earlier date.
6. Preserve unusual but officially compliant instruments rather than deleting
   them by assumption.
7. Normalize ticker symbols to uppercase and trim spaces.
8. Record every applied source and effective interval.

## New files

```text
data/reference/kmi_all_share_membership_history.csv
data/reference/kmi_all_share_membership_history.parquet

src/psx_ml/c10/build_kmi_all_share_membership.py
src/psx_ml/c10/kmi_all_share_membership.py

tests/c10/test_kmi_all_share_membership.py

artifacts/reports/C10_CP4B_KMI_ALL_SHARE_MEMBERSHIP_REPORT.md
artifacts/reports/C10_CP4B_KMI_ALL_SHARE_MEMBERSHIP_MANIFEST.json
```

## Membership schema

```text
symbol
effective_from
effective_to
review_from
review_to
notice_date
notice_no
source_url
source_type
shariah_compliant
```

Rules:

- `effective_from` inclusive
- `effective_to` inclusive
- final research interval may use `9999-12-31`
- `shariah_compliant` must always be true in the membership artifact
- no duplicate `symbol + effective_from`
- no overlapping intervals for a symbol
- no interval beginning in 2026 for this checkpoint

## CP4B-1 acceptance tests

```text
1. First effective interval covers 2023-01-02 signal date.
2. All effective intervals are ordered and non-overlapping.
3. Every interval has an official PSX source URL.
4. Every interval has a notice date no later than effective_from.
5. No 2026 recomposition is used.
6. No symbol is present twice in the same effective interval.
7. Membership counts are plausible and reconciled to official notices.
8. Applying incoming/outgoing changes reproduces the next interval exactly.
9. CSV and Parquet content hashes are recorded.
10. Full tests/c10 suite passes.
```

Run:

```bash
python -m py_compile \
  src/psx_ml/c10/kmi_all_share_membership.py \
  src/psx_ml/c10/build_kmi_all_share_membership.py

pytest -q tests/c10

python -m psx_ml.c10.build_kmi_all_share_membership
```

Stop after CP4B-1 and inspect the generated interval counts and reconciliation
report before generating P5 selections.

---

# Checkpoint CP4B-2 — Generate P5 selections

## Policy identity

```text
policy_id: P5_shariah_all_share
model_name: lightgbm_cpu
horizon: 5
target_family: market_relative
feature_variant: B_market_context
rebalance: weekly first session
universe: point-in-time PSX-KMI All Share
liquidity_filter: exclude bottom 25% within date
selection: top 10% after liquidity filtering
sector_cap: 2
```

## Selection sequence

For each accepted weekly signal date:

1. Load accepted C8 OOF validation predictions.
2. Keep:
   - `horizon == 5`
   - `target_family == "market_relative"`
   - `feature_variant == "B_market_context"`
   - `model_name == "lightgbm_cpu"`
3. Join the latest effective KMI All Share membership interval.
4. Remove non-members.
5. Join point-in-time `turnover_median_20obs_adj` using latest observation on
   or before the signal date.
6. Do not use future liquidity observations.
7. Exclude rows with missing or nonpositive liquidity.
8. Rank liquidity within the eligible P5 universe on each signal date.
9. Remove the bottom 25% by liquidity.
10. Rank remaining candidates by prediction descending.
11. Select `ceil(candidate_count * 0.10)`.
12. Apply maximum two selections per sector while walking the ranked list.
13. Preserve deterministic tie-breaking:
    - prediction descending
    - liquidity descending
    - symbol ascending
14. Store all membership, liquidity, ranking, and source audit fields.

## New files

```text
src/psx_ml/c10/p5_selection.py
src/psx_ml/c10/build_p5_selections.py

tests/c10/test_p5_selection.py

data/processed/c10/p5_shariah_all_share_selections.parquet

artifacts/reports/C10_CP4B_P5_SELECTION_REPORT.md
artifacts/reports/C10_CP4B_P5_SELECTION_MANIFEST.json
```

## Required selection columns

```text
policy_id
trade_date
symbol
fold_id
horizon
target_family
feature_variant
model_name
prediction
sector
selection_date
selection_tail
shariah_member
shariah_candidate_count_before_liquidity
liquidity_observation_date
liquidity_age_days
turnover_median_20obs_adj
liquidity_percentile_rank
liquidity_filter_pass
shariah_candidate_count_after_liquidity
selection_target_count
selection_rank
effective_from
effective_to
review_from
review_to
notice_date
notice_no
source_url
source_type
```

## CP4B-2 acceptance tests

```text
1. Policy ID is only P5_shariah_all_share.
2. Signal dates exactly match P1 and P4.
3. No selection occurs outside effective membership.
4. No future membership or liquidity observation is used.
5. No 2026 row exists.
6. All selected rows pass the liquidity filter.
7. Sector count never exceeds two per date.
8. Selection count equals ceil(post-liquidity candidates × 10%), unless the
   sector cap prevents enough names; any shortfall must be reported.
9. Ranking and tie-breaking are deterministic.
10. No duplicate policy/date/symbol or date/rank keys.
11. Manifest hash matches the generated Parquet.
12. Full tests/c10 suite passes.
```

Run:

```bash
python -m py_compile \
  src/psx_ml/c10/p5_selection.py \
  src/psx_ml/c10/build_p5_selections.py

pytest -q tests/c10

python -m psx_ml.c10.build_p5_selections
```

Stop and inspect:

```text
rows
signal dates
unique symbols
minimum/median/maximum holdings
candidate counts before liquidity filtering
candidate counts after liquidity filtering
sector-cap shortfalls
membership interval coverage
liquidity observation ages
```

---

# Checkpoint CP4B-3 — Integrate P5 into C10 checkpoints

## Required changes

Update:

```text
src/psx_ml/c10/inputs.py
src/psx_ml/c10/policies.py
src/psx_ml/c10/checkpoint1.py
src/psx_ml/c10/checkpoint2.py
tests/c10/test_p5_c10_integration.py
```

Do not add P3 to executable policy outputs.

Final executable policy set:

```text
P1_broad_canonical
P2_conservative_consensus
P4_kmi30_strict
P5_shariah_all_share
```

## Frozen P5 policy

```python
P5_SHARIAH_ALL_SHARE = FrozenPolicy(
    policy_id="P5_shariah_all_share",
    models=("lightgbm_cpu",),
    target="fwd_market_relative_rank_5s",
    feature_variant="B_market_context",
    selection=(
        "top_10pct_within_point_in_time_kmi_all_share_"
        "after_bottom_25pct_liquidity_exclusion"
    ),
    rebalance="weekly_first_session",
    sector_cap=2,
    liquidity_screen="bottom_25pct_excluded",
)
```

## Preservation requirement

Before overwriting CP2 outputs, compare regenerated P1/P2/P4 rows against the
currently accepted ledgers:

```text
frictionless_trades.parquet
frictionless_positions.parquet
frictionless_nav.parquet
```

Comparison keys must be deterministic and numeric tolerances must remain:

```text
rtol = 1e-12
atol = 1e-9
```

Abort before writing if any P1/P2/P4 row changes.

## Run

```bash
python -m py_compile \
  src/psx_ml/c10/inputs.py \
  src/psx_ml/c10/policies.py \
  src/psx_ml/c10/checkpoint1.py \
  src/psx_ml/c10/checkpoint2.py

pytest -q tests/c10

python -m psx_ml.c10.checkpoint1
python -m psx_ml.c10.checkpoint2
python -m psx_ml.c10.checkpoint3
python -m psx_ml.c10.checkpoint4
```

## Expected policy coverage

All outputs below must contain exactly P1, P2, P4 and P5:

```text
data/processed/c10/frictionless_trades.parquet
data/processed/c10/frictionless_positions.parquet
data/processed/c10/frictionless_nav.parquet
data/processed/c10/costed_trades.parquet
data/processed/c10/costed_nav.parquet
data/processed/c10/cost_summary.parquet
data/processed/c10/capacity_trade_diagnostics.parquet
data/processed/c10/capacity_summary.parquet
data/processed/c10/capacity_limits.parquet
```

## Expected row-count formulas

Do not hardcode P5 counts before selection generation.

```text
CP2 NAV rows:
741 × 4 policies = 2,964

CP3 cost NAV rows:
741 × 4 policies × 4 cost schedules = 11,856

CP3 summary rows:
4 policies × 4 cost schedules = 16

CP4 capacity summary rows:
5 capital levels × 3 participation rates × 4 policies = 60

CP4 capacity-limit rows:
3 participation rates × 4 policies = 12
```

---

# Final CP4B audit

Generate:

```text
artifacts/reports/C10_CP4B_P5_FINAL_AUDIT.md
artifacts/reports/C10_CP4B_P5_FINAL_MANIFEST.json
```

The final audit must show:

## Universe integrity

```text
No non-member selections
No interval violations
No future source usage
No 2026 rows
No blanket sector assumptions
Official PSX source on every membership interval
```

## Portfolio integrity

```text
100% entry availability or explicit failure
No future price use
Exact NAV identity
No duplicate trades/positions/NAV keys
P1/P2/P4 preserved
```

## Policy comparison

For P1/P2/P4/P5 report:

```text
frictionless ending NAV
frictionless annualized return
frictionless volatility
frictionless Sharpe
frictionless maximum drawdown

actual-all-in ending net NAV
actual-all-in annualized return
actual-all-in volatility
actual-all-in Sharpe
actual-all-in maximum drawdown
total transaction costs
weighted average cost rate

capacity at PKR 1m / 5m / 10m
at 5%, 10%, 20% participation
```

## Interpretation required

The final report must explicitly answer:

```text
Does P5 reduce P4 concentration risk?
Does P5 preserve P4's liquidity advantage?
Does P5 improve or weaken net risk-adjusted performance?
How many P5 candidates and holdings are generated per date?
How much of P5's universe is practically tradable at PKR 1m, 5m and 10m?
Is P5 a better live candidate than P4?
```

---

# Commit only after acceptance

```bash
git status --short

git add \
  data/reference/kmi_all_share_membership_history.csv \
  data/reference/kmi_all_share_membership_history.parquet \
  data/processed/c10 \
  src/psx_ml/c10 \
  tests/c10 \
  artifacts/reports

git commit -m "C10: add point-in-time Shariah all-share P5 policy"

git push
```

Do not merge until:

```text
all tests pass
all CP4B acceptance checks pass
P1/P2/P4 preservation checks pass
membership sources are reviewed
P5 final comparison is accepted
```

---

# Recommended execution order after returning

```bash
# 1. Ensure existing P4 work is committed first.
git status --short

# 2. Create P5 branch.
git switch -c feature/c10-p5-shariah-all-share

# 3. Implement and run CP4B-1 only.
# Stop and review membership history.

# 4. Implement and run CP4B-2 only.
# Stop and review P5 selections.

# 5. Implement CP4B-3.
# Run CP1, CP2, CP3 and CP4.

# 6. Run final audit.
# Commit only after acceptance.
```
