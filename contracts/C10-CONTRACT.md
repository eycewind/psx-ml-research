# C10 — Fee-Aware Portfolio Construction and Execution Backtest

## 1. Contract identity

- **Project:** `psx-ml-research`
- **Contract:** `C10_FEE_AWARE_PORTFOLIO_AND_EXECUTION_BACKTEST`
- **Required branch:** `feature/c10-fee-aware-portfolio-backtest`
- **Base:** accepted C9 merged into `main`
- **Primary policy:** `P1_broad_canonical`
- **Conservative policy:** `P2_conservative_consensus`
- **Primary horizon:** 5 sessions
- **Canonical rebalance:** weekly first session
- **Final 2026 holdout:** remains locked
- **Primary purpose:** determine whether the predictive candidate-selection advantage found in C9 survives realistic PSX trading frictions, portfolio construction, turnover, cash constraints and execution assumptions.

C10 must be implemented, reviewed and accepted on its own branch. It must not be merged into `main` until all acceptance tests pass and the contract is explicitly accepted.

## 2. Motivation

C9 accepted two frozen candidate-selection policies.

### P1 — Broad canonical

```text
model: LightGBM
target: 5-session market-relative rank
features: B_market_context
selection: top 10%
rebalance: weekly first session
sector cap: max 2 per sector
liquidity: canonical universe
```

### P2 — Conservative consensus

```text
models: LightGBM + XGBoost
selection: intersection of top 10%
rebalance: weekly first session
sector cap: max 2 per sector
liquidity: top 75% by turnover
```

C9 established predictive robustness but did not test implementable profitability.

C10 asks:

> After realistic costs, execution rules and portfolio constraints, do P1 or P2 produce positive and robust net portfolio results?

## 3. Scope

### In scope

- deterministic portfolio construction;
- equal-weight and constrained weighting;
- weekly rebalancing;
- position entry and exit;
- portfolio cash accounting;
- brokerage and statutory transaction costs;
- bid–ask spread and slippage assumptions;
- turnover and implementation shortfall;
- liquidity and participation constraints;
- gross and net returns;
- volatility, Sharpe, Sortino and drawdown;
- capacity and break-even cost analysis;
- benchmark comparison;
- Signal Viewer-compatible summaries.

### Out of scope

- live execution or broker APIs;
- intraday order-book simulation;
- leverage, short selling, derivatives or margin;
- stop-loss or take-profit optimization;
- predictive-model retraining;
- feature or target redefinition;
- hyperparameter optimization;
- 2026 holdout access;
- news and deep learning.

## 4. Source boundaries

Expected inputs:

```text
artifacts/c9/
artifacts/reports/C9_SELECTION_REPORT.md
artifacts/reports/C9_POLICY_DECISION.md
artifacts/reports/C9_MANIFEST.json
data/processed/c9/
data/processed/features/
data/processed/universe/
data/processed/datasets/temporal_split_assignments.parquet
config/
```

C10 must not:

- connect to SQLite;
- read or modify `psx_watcher.db`;
- modify `psx-stock-watcher`;
- alter C8/C9 predictions;
- change P1/P2 definitions;
- retrain models;
- access 2026 final-holdout rows;
- overwrite C1–C9 outputs;
- use future information for execution decisions.

## 5. Frozen policy definitions

### P1

```text
policy_id: P1_broad_canonical
model: LightGBM
target: fwd_market_relative_rank_5s
features: B_market_context
selection: top_10pct
rebalance: weekly_first_session
sector_cap: 2
liquidity_screen: L0
```

### P2

```text
policy_id: P2_conservative_consensus
models: LightGBM + XGBoost
selection: intersection_top_10pct
rebalance: weekly_first_session
sector_cap: 2
liquidity_screen: L1
```

No C10 result may change these definitions.

## 6. Backtest timeline

For each weekly signal date `t`:

1. Use only information available by the end of `t`.
2. Form the candidate list from the frozen C9 policy.
3. Execute entries on the next valid tradable session.
4. Hold until the next scheduled rebalance.
5. Process exits before entries.
6. Carry unallocated capital as cash.
7. Apply and record every cost component.
8. Reject look-ahead in price, liquidity and corporate-action data.

Canonical timing:

```text
signal date: t
entry date: next valid session
entry price: next_open
exit date: next rebalance execution date
```

Required execution-price variants:

```text
next_open
next_vwap_proxy if available
next_close sensitivity only
```

## 7. Price basis and corporate actions

Required:

- confirm adjusted versus unadjusted fields;
- use one consistent price basis;
- reject mixed adjusted/unadjusted execution and valuation;
- detect missing prices, suspensions and stale values;
- document delisting and long-suspension handling;
- do not silently impute execution prices.

## 8. Portfolio construction

Canonical weighting:

```text
equal_weight
```

Required sensitivities:

```text
equal_weight
inverse_volatility
liquidity_capped_equal_weight
```

Inverse volatility must use trailing data only. No optimized weights are allowed.

## 9. Capital assumptions

Required:

```text
PKR 1,000,000
PKR 5,000,000
PKR 10,000,000
PKR 50,000,000
```

Canonical:

```text
PKR 5,000,000
```

Required:

- whole-share constraints;
- deterministic rounding;
- minimum position values;
- residual cash accounting.

## 10. Position constraints

Canonical:

```text
max single-position weight = 15%
max sector weight = 30%
minimum position value = PKR 25,000
```

Sensitivity:

```text
single-position cap: 10%, 15%, 20%
sector cap: 20%, 30%, 40%
minimum position: PKR 10k, 25k, 50k
```

Residual capital remains cash.

## 11. Rebalance logic

Required:

```text
weekly full rebalance
weekly retain-selected
weekly buffered
non-overlapping 5-session
```

Buffered rule:

```text
enter inside top 10%
retain while inside top 15%
exit outside top 15%
```

Thresholds are fixed before evaluation.

## 12. Transaction-cost model

Separate:

```text
brokerage
statutory charges
spread
slippage
market impact
```

### Brokerage placeholder

Until verified:

```text
0.15% per side
minimum PKR 0.03 per share
```

Use:

```text
max(rate-based charge, per-share minimum)
```

only if confirmed by the broker schedule.

### Statutory components

Store separately, for example:

```text
PSX
NCCPL
CDC
SECP levy
sales tax
other applicable levies
```

Canonical acceptance requires verified current rates.

### Spread scenarios per side

```text
0.05%
0.10%
0.20%
0.30%
```

Provisional base:

```text
0.10%
```

### Slippage scenarios per side

```text
0.00%
0.05%
0.10%
0.20%
```

Provisional base:

```text
0.05%
```

### Market impact

Required sensitivity:

```text
impact = coefficient * participation_rate
```

A zero coefficient is allowed only as a documented provisional case.

## 13. Liquidity and capacity

Required ADV caps:

```text
2%
5%
10%
```

Canonical:

```text
5% of trailing 20-session average daily traded value
```

Report rejected/clipped positions, residual cash, effective position count and participation.

## 14. Execution rules

Required:

- sells before buys;
- cash updated after sells and costs;
- buys clipped to cash and ADV limits;
- no negative cash;
- no fractional shares unless configured;
- no trading on invalid prices;
- deterministic allocation order.

Canonical allocation order:

```text
descending model rank
```

Sensitivity:

```text
pro-rata allocation
```

## 15. Daily valuation

Required fields:

```text
trade_date
cash
gross_market_value
net_liquidation_value
gross_exposure
net_exposure
position_count
sector_count
daily_gross_return
daily_net_return
cumulative_gross_return
cumulative_net_return
```

## 16. Performance metrics

Required:

```text
total gross/net return
annualized gross/net return
annualized volatility
Sharpe ratio
Sortino ratio
maximum drawdown
Calmar ratio
positive-day fraction
positive-week fraction
best/worst day
best/worst week
```

Risk-free rate must be configurable. Initial canonical assumption:

```text
0%
```

## 17. Benchmarks

Required:

```text
cash
equal-weight eligible universe
C9 random same-count
C9 momentum
C9 liquidity
KSE-100 if compatible data exists
KMI-30 if compatible data exists
```

Label price-index versus total-return comparisons explicitly.

## 18. Cost attribution

Required:

```text
gross return
brokerage drag
statutory drag
spread drag
slippage drag
market-impact drag
cash drag
constraint drag
net return
```

## 19. Turnover

Required:

```text
one-way turnover
two-way turnover
weekly turnover
annualized turnover
entry turnover
exit turnover
buffered-turnover reduction
```

All must reconcile with transaction records.

## 20. Break-even analysis

Required:

```text
maximum round-trip cost preserving positive total return
maximum round-trip cost preserving positive annualized return
maximum per-side cost preserving Sharpe > 0
maximum cost preserving benchmark outperformance
```

Cost grid:

```text
0.00% to 1.50% round trip
step 0.05%
```

## 21. Cost scenarios

### C0 — Frictionless

### C1 — Brokerage only

### C2 — Brokerage + statutory

### C3 — Base realistic

```text
brokerage + statutory + 0.10% spread per side + 0.05% slippage per side
```

### C4 — Conservative

```text
brokerage + statutory + 0.20% spread per side + 0.10% slippage per side
```

### C5 — Severe

```text
brokerage + statutory + 0.30% spread per side + 0.20% slippage per side
```

No canonical conclusion may rely only on C0/C1.

## 22. Policy comparison

Compare P1 and P2 on:

```text
gross/net return
Sharpe
drawdown
turnover
cost drag
cash drag
capacity
position count
sector concentration
benchmark excess return
```

## 23. Sensitivities

Required:

```text
rebalance mode
weighting method
capital level
cost scenario
ADV cap
position cap
sector cap
minimum position value
```

No sensitivity may change the predictive policy definition.

## 24. Fold evaluation

Required:

```text
fold_2023
fold_2024
fold_2025
stitched OOF portfolio
```

Only valid OOF predictions may be used.

## 25. Concentration

Required:

```text
top contributing/detracting dates
top contributing/detracting symbols
top contributing/detracting sectors
date/symbol/sector Herfindahl metrics
leave-top-5-dates-out
leave-top-10-dates-out
leave-top-symbol-out
leave-top-sector-out
```

## 26. Robustness gates

A positive result should satisfy most of:

- positive net return under C3;
- positive in at least 2 of 3 folds;
- no catastrophic fold;
- positive benchmark excess return;
- positive after top-date and top-symbol removal;
- realistic ADV participation;
- acceptable cash drag;
- break-even cost above base cost;
- no dependence on one exact capital or weighting choice.

## 27. Signal Viewer compatibility

Generate summaries for:

```text
policy
cost scenario
capital
weighting
rebalance
fold
benchmark
sector
symbol
```

Required datasets:

```text
gross/net equity curves
drawdown
cost attribution
turnover
cash exposure
position count
sector exposure
break-even cost
capital-capacity
fold/policy/benchmark comparisons
```

Viewer code changes remain separate.

## 28. Outputs

Required reports:

```text
artifacts/reports/C10_BACKTEST_REPORT.md
artifacts/reports/C10_COST_REPORT.md
artifacts/reports/C10_EXECUTION_REPORT.md
artifacts/reports/C10_CAPACITY_REPORT.md
artifacts/reports/C10_POLICY_COMPARISON.md
artifacts/reports/C10_ROBUSTNESS_REPORT.md
artifacts/reports/C10_DELIVERY.md
artifacts/reports/C10_MANIFEST.json
artifacts/reports/C10_WORKLOG.md
```

Required structured artifacts:

```text
artifacts/c10/portfolio_metrics.parquet
artifacts/c10/scenario_metrics.parquet
artifacts/c10/transaction_metrics.parquet
artifacts/c10/break_even_metrics.parquet
artifacts/c10/viewer_summary.json
```

Suggested runtime data:

```text
data/processed/c10/
├── portfolio_daily.parquet
├── positions.parquet
├── transactions.parquet
├── executions.parquet
├── cost_attribution.parquet
├── benchmark_daily.parquet
├── scenario_metrics.parquet
├── break_even_metrics.parquet
├── capacity_metrics.parquet
└── viewer_summaries/
```

## 29. Manifest requirements

Record:

```text
version and timestamp
branch and generation commit
dirty state
input and C9 hashes
frozen policy definitions
price-source hashes
corporate-action assumptions
cost parameters
execution rules
capital and weighting scenarios
rebalance and liquidity constraints
benchmark definitions
holdout flag
row/trade/position/scenario counts
fold and policy metrics
cost attribution
break-even and capacity results
output and logical hashes
runtime statistics
```

Timestamps must not affect logical hashes.

## 30. Suggested architecture

```text
src/psx_ml/c10/
├── inputs.py
├── policies.py
├── prices.py
├── corporate_actions.py
├── portfolio.py
├── weights.py
├── constraints.py
├── execution.py
├── costs.py
├── capacity.py
├── accounting.py
├── benchmarks.py
├── metrics.py
├── break_even.py
├── scenarios.py
├── robustness.py
├── reports.py
├── manifest.py
└── pipeline.py
```

## 31. Acceptance tests

### Safety and provenance

1. Runs only on `feature/c10-fee-aware-portfolio-backtest`.
2. Starts from accepted C9 on `main`.
3. Remains unmerged until explicit acceptance.
4. No SQLite access.
5. Watcher repo and DB unchanged.
6. C1–C9 artifacts not overwritten.
7. C9 hashes reconcile.
8. P1/P2 definitions exactly match C9.
9. No retraining or feature/target changes.
10. Only OOF predictions used.
11. 2026 access fails by default.
12. Manifest records `holdout_accessed=false`.

### Price and timing

13. Selection uses signal-date information only.
14. Execution uses next valid session.
15. Entry/exit price basis is consistent.
16. Adjusted/unadjusted mixing is rejected.
17. Missing, stale and suspended prices are explicit.
18. Future-row append does not alter prior trades.

### Portfolio and execution

19. Equal weights reconcile.
20. Inverse-volatility uses trailing data only.
21. Position/sector caps are enforced.
22. Whole-share rounding is deterministic.
23. Minimum position value enforced.
24. Sells occur before buys.
25. Cash never becomes negative.
26. Executions reconcile with transactions.
27. Transactions reconcile with positions.
28. Positions and cash reconcile with NAV.

### Costs and capacity

29. Brokerage percentage is correct.
30. Per-share minimum is correct.
31. Statutory charges are itemized.
32. Spread/slippage applied per side.
33. Market impact formula is correct.
34. Gross-to-net attribution reconciles.
35. ADV is trailing and point-in-time.
36. Participation caps are enforced.
37. Clipping and cash drag reconcile.

### Metrics and benchmarks

38. Gross/net returns are correct.
39. Annualization is correct.
40. Volatility, Sharpe and Sortino are correct.
41. Drawdown and Calmar are correct.
42. Turnover reconciles.
43. Benchmark dates align.
44. Baseline results reconcile.
45. Index benchmark type is labeled.

### Scenarios and robustness

46. C0–C5 reconcile.
47. Break-even grid is deterministic.
48. Policy comparisons use identical dates.
49. Capital/weighting/rebalance sensitivities use frozen policy logic.
50. Fold portfolios use OOF predictions only.
51. Stitched OOF portfolio reconciles.
52. Leave-out diagnostics reconcile.
53. Concentration metrics reconcile.

### Delivery

54. Repeated runs produce identical logical hashes.
55. CPU C1–C10 suite passes.
56. Reports generated from a clean commit.
57. Manifest records correct generation commit.
58. Viewer summaries generated.
59. Report counts reconcile with artifacts.
60. No live signal is produced.
61. No unsupported profitability claim is made.
62. Final 2026 holdout remains untouched.

## 32. Required implementation sequence

1. Confirm C9 is merged and tagged.
2. Create the C10 branch.
3. Add and commit this contract.
4. Freeze P1/P2 in configuration.
5. Validate C9 predictions and hashes.
6. Audit execution-price fields.
7. Audit corporate actions.
8. Verify broker and PSX cost rates.
9. Freeze provisional/canonical costs.
10. Implement execution timing.
11. Implement equal-weight portfolio and cash accounting.
12. Implement transaction costs.
13. Implement capacity constraints.
14. Implement daily valuation and metrics.
15. Implement benchmarks and scenarios.
16. Implement break-even analysis.
17. Implement fold and stitched portfolios.
18. Implement P1/P2 and sensitivity comparisons.
19. Implement concentration/leave-out robustness.
20. Generate reports, artifacts and viewer summaries.
21. Run the full CPU suite.
22. Commit implementation.
23. Regenerate from a clean commit.
24. Push for review.
25. Do not merge before explicit acceptance.

## 33. Manual worklog

Maintain:

```text
artifacts/reports/C10_WORKLOG.md
```

Each entry records:

```text
date/time
branch
commit
objective
files changed
commands run
tests run
results
known limitations
next step
```

Work in small slices, test each slice, commit accepted work and do not batch unrelated changes.

## 34. Acceptance decision

### ACCEPT

At least one frozen C9 policy remains viable under realistic costs and constraints, survives at least 2 of 3 folds, has acceptable drawdown, exceeds appropriate benchmarks and has break-even costs above the base assumption.

### ACCEPT WITH LIMITATIONS

Viability exists only under narrow capital, cost, liquidity, turnover or rebalance conditions.

### REJECT

The C9 predictive advantage does not survive realistic implementation.

Final question:

> Does the C9 ranking signal remain economically viable after realistic PSX implementation costs and portfolio constraints?
