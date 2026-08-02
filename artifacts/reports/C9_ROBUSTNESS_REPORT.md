# C9 Robustness Report

All folds, thresholds, schedules, liquidity screens and sector caps retain explicit counts. C8 regime labels are preserved as accepted quantile labels.

## Frozen robustness gates

{
  "concentration_leaveout": true,
  "nearby_liquidity_sector_model_schedule": true,
  "random_baseline": true
}

## Nearby and structural comparisons

| comparison | mean_outcome | positive_all_folds | positive_ci |
|---|---|---|---|
| E0_lightgbm|top_5pct|weekly_first_session|L0|S1 | 0.013694037056308457 | True | True |
| E0_lightgbm|top_20pct|weekly_first_session|L0|S1 | 0.012098124075728358 | True | True |
| E0_lightgbm|top_10pct|weekly_first_session|L1|S1 | 0.012580561833207866 | True | True |
| E0_lightgbm|top_10pct|weekly_first_session|L2|S1 | 0.011820758999034677 | True | True |
| E0_lightgbm|top_10pct|weekly_first_session|L0|S0 | 0.012552146994815215 | True | True |
| E0_lightgbm|top_10pct|weekly_first_session|L0|S2 | 0.01327719093582419 | True | True |
| E1_xgboost|top_10pct|weekly_first_session|L0|S1 | 0.011539638454922578 | True | True |
| E0_lightgbm|top_10pct|non_overlapping_5_session|L0|S1 | 0.01055416885640521 | True | True |

## Concentration leave-outs

| dimension | group_count | base_row_mean | top_5_positive_contribution_share | top_10_positive_contribution_share | top_20_positive_contribution_share | leave_top_1_out_mean | leave_top_3_out_mean | leave_top_5_out_mean | leave_top_10_out_mean |
|---|---|---|---|---|---|---|---|---|---|
| trade_date | 157 | 0.01297836978460743 | 0.14005064512788157 | 0.24277443154940545 | 0.38780697550016635 | — | — | 0.01126307963544874 | 0.010015683338660918 |
| symbol | 249 | 0.01297836978460743 | 0.13143281805600346 | 0.22128380481039067 | 0.3645888495426444 | — | — | 0.011861769033244212 | 0.011180845736229239 |
| sector | 34 | 0.01297836978460743 | 0.4286524942902016 | 0.6832660043303295 | 0.9299286941227314 | 0.012518560652215821 | 0.01118572589447264 | — | — |

## Bottom-tail avoidance

| excluded_fraction | excluded_rows | bottom_mean_outcome | remaining_universe_mean_outcome |
|---|---|---|---|
| 0.05 | 7781 | 0.007309829334826366 | 0.009368557088995668 |
| 0.1 | 15142 | 0.005739153724195885 | 0.009661604218125478 |
| 0.2 | 29894 | 0.005950869056324183 | 0.010097901270655607 |
