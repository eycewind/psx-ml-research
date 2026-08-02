# C9 Delivery Report

Status: **ACCEPT**

Generation commit: `fe1e955bfed7dea5d6e5fbc87dfa5e77ff05f6e3`; dirty: **True**; holdout accessed: **false**.

## Decision

Freeze `P1_broad_canonical` as the primary C10 candidate and `P2_conservative_consensus` as the conservative alternative. P1 has mean date-level market-relative outcome `0.012571053`, spread versus unselected `0.004773205`, positive-date fraction `0.7834`, and a 95% outcome interval `[0.0090831885, 0.016163048]`. P2 has mean outcome `0.013231001` and interval `[0.009562125, 0.017041361]`. Both are positive in all three folds.

P1 exceeds the deterministic same-count random mean `0.0081320905` with empirical p-value `0.001998`. Nearby 5% and 20% thresholds, L1/L2 liquidity screens, S0/S2 sector constraints, XGBoost, and the non-overlapping schedule retain positive fold and bootstrap gates. Date, symbol, and sector leave-outs remain positive. Mean LightGBM/XGBoost rank correlation is `0.933487`.

C9 evaluates predictive candidate-selection robustness only. It does not include fees, spreads, slippage, portfolio accounting, P&L, Sharpe, drawdown, live signals or a profitability claim. The final 2026 holdout remains untouched.
