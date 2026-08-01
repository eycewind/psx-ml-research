# C7 Feature Importance Report

Importance is associational, not causal. Permutation importance uses deterministic validation samples without refitting.

| Model | Feature | Mean permutation importance | Fold/task std |
|---|---|---:|---:|
| `lightgbm_cpu` | `eligible_symbol_count` | 0.0020008536 | 0.0041732525 |
| `lightgbm_cpu` | `market_median_ret_1obs_adj` | 0.00082552987 | 0.0020467251 |
| `lightgbm_cpu` | `ret_20obs_adj` | 0.00034071658 | 0.0010495587 |
| `lightgbm_cpu` | `close_to_max_20obs_adj` | 0.0001800613 | 0.0004553966 |
| `lightgbm_cpu` | `atr_mean_20obs_adj` | 0.00017860841 | 0.00050054767 |
| `lightgbm_cpu` | `rv_20obs_adj` | 8.1019633e-05 | 0.00016429799 |
| `lightgbm_cpu` | `close_to_mean_20obs_adj` | 6.4686748e-05 | 0.00012275675 |
| `lightgbm_cpu` | `turnover_median_20obs_adj` | 4.66079e-05 | 0.00019501652 |
| `lightgbm_cpu` | `ret_5obs_adj` | 4.5531957e-05 | 0.0001097442 |
| `lightgbm_cpu` | `amihud_mean_20obs_adj` | -3.5841752e-05 | 9.6724299e-05 |
| `lightgbm_cpu` | `ret_20obs_rank_adj` | 3.422417e-05 | 0.00030769647 |
| `lightgbm_cpu` | `days_since_previous_observation` | -2.5834718e-05 | 6.283836e-05 |
| `lightgbm_cpu` | `turnover_rank_adj` | -1.6335077e-05 | 4.2094621e-05 |
| `lightgbm_cpu` | `close_to_open_1obs_adj` | 1.2924959e-05 | 3.0152454e-05 |
| `lightgbm_cpu` | `true_range_1obs_adj` | 7.6309244e-06 | 2.7512131e-05 |
| `lightgbm_cpu` | `log_ret_20obs_adj` | 6.4004922e-06 | 3.2332213e-05 |
| `lightgbm_cpu` | `turnover_1obs_adj` | -5.5120249e-06 | 1.4935706e-05 |
| `lightgbm_cpu` | `ret_1obs_adj` | 3.957511e-06 | 1.2161281e-05 |
| `lightgbm_cpu` | `log1p_volume_adj` | -1.0590283e-06 | 3.8083936e-05 |
| `lightgbm_cpu` | `volume_ratio_median_20obs_adj` | -5.6451789e-07 | 4.2534142e-06 |
| `lightgbm_cpu` | `unchanged_close_fraction_20obs` | 4.2515863e-07 | 1.707571e-06 |
| `lightgbm_cpu` | `open_gap_1obs_adj` | 3.2612512e-07 | 1.4080346e-05 |
| `lightgbm_cpu` | `log_ret_1obs_adj` | 2.0253625e-07 | 1.31059e-06 |
| `lightgbm_cpu` | `missing_volume_flag` | 0 | 0 |
| `lightgbm_cpu` | `stale_close_run_length` | 0 | 0 |
| `lightgbm_cpu` | `strict_high_below_low_flag` | 0 | 0 |
| `lightgbm_cpu` | `zero_volume_flag` | 0 | 0 |
| `xgboost_gpu` | `eligible_symbol_count` | 0.0021835241 | 0.0043797668 |
| `xgboost_gpu` | `market_median_ret_1obs_adj` | 0.00098138477 | 0.0024795246 |
| `xgboost_gpu` | `ret_20obs_adj` | 0.00031877589 | 0.00076318425 |
| `xgboost_gpu` | `atr_mean_20obs_adj` | 0.00028479156 | 0.00084126649 |
| `xgboost_gpu` | `close_to_max_20obs_adj` | 0.00022309845 | 0.0005020693 |
| `xgboost_gpu` | `ret_20obs_rank_adj` | -0.00018624286 | 0.00035278556 |
| `xgboost_gpu` | `ret_5obs_adj` | 0.00015570707 | 0.00038027588 |
| `xgboost_gpu` | `amihud_mean_20obs_adj` | -0.00011054193 | 0.00041352262 |
| `xgboost_gpu` | `close_to_mean_20obs_adj` | 0.00010402259 | 0.00023135274 |
| `xgboost_gpu` | `turnover_median_20obs_adj` | 7.9458733e-05 | 0.00017956913 |
| `xgboost_gpu` | `rv_20obs_adj` | 7.9278266e-05 | 0.0002317078 |
| `xgboost_gpu` | `close_to_open_1obs_adj` | 6.1737199e-05 | 0.00014563029 |
| `xgboost_gpu` | `log_ret_20obs_adj` | 2.7966577e-05 | 8.8549296e-05 |
| `xgboost_gpu` | `turnover_rank_adj` | -2.0310204e-05 | 4.2622869e-05 |
| `xgboost_gpu` | `log1p_volume_adj` | -1.808613e-05 | 6.3223561e-05 |
| `xgboost_gpu` | `true_range_1obs_adj` | 1.091053e-05 | 2.5488217e-05 |
| `xgboost_gpu` | `open_gap_1obs_adj` | 6.7384119e-06 | 3.3912807e-05 |
| `xgboost_gpu` | `unchanged_close_fraction_20obs` | -6.4554889e-06 | 4.1268649e-05 |
| `xgboost_gpu` | `ret_1obs_adj` | -4.4553927e-06 | 1.5457192e-05 |
| `xgboost_gpu` | `days_since_previous_observation` | -4.0663232e-06 | 2.6053001e-05 |
| `xgboost_gpu` | `log_ret_1obs_adj` | -2.6882318e-06 | 9.6302644e-06 |
| `xgboost_gpu` | `turnover_1obs_adj` | -2.1235948e-06 | 1.6690353e-05 |
| `xgboost_gpu` | `volume_ratio_median_20obs_adj` | -1.0097837e-06 | 1.8031998e-05 |
| `xgboost_gpu` | `missing_volume_flag` | 0 | 0 |
| `xgboost_gpu` | `stale_close_run_length` | 0 | 0 |
| `xgboost_gpu` | `strict_high_below_low_flag` | 0 | 0 |
| `xgboost_gpu` | `zero_volume_flag` | 0 | 0 |
