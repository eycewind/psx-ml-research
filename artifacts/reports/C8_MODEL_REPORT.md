# C8 Model Evaluation Report

These are leakage-safe predictive validation diagnostics, not signals, backtests, portfolios, or profitability results.

## Fold stability

| Stage | Horizon | Target | Features | Model | Subset | Mean daily IC | IC 95% CI | Fold std | Worst | Best | Positive folds | Mean D10-D1 | D10 95% CI | Positive spread folds |
|---:|---:|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---|---:|
| 1 | 5 | `absolute` | `A_c7_only` | `hist_gradient_boosting_cpu` | `natural_coverage` | 0.0419956 | [0.033392, 0.050411] | 0.0107719 | 0.0271875 | 0.0524965 | 3 | 0.00808861 | [0.0057031, 0.011103] | 3 |
| 1 | 5 | `absolute` | `A_c7_only` | `hist_gradient_boosting_cpu` | `stage1_common_matched` | 0.0419956 | [0.033392, 0.050411] | 0.0107719 | 0.0271875 | 0.0524965 | 3 | 0.00808861 | [0.0057031, 0.011103] | 3 |
| 1 | 5 | `absolute` | `A_c7_only` | `lightgbm_cpu` | `natural_coverage` | 0.0221228 | [0.01804, 0.035697] | 0.0171185 | 0.00776648 | 0.0461825 | 3 | 0.00212703 | [9.8371e-05, 0.0045286] | 2 |
| 1 | 5 | `absolute` | `A_c7_only` | `lightgbm_cpu` | `stage1_common_matched` | 0.0221228 | [0.01804, 0.035697] | 0.0171185 | 0.00776648 | 0.0461825 | 3 | 0.00212703 | [9.8371e-05, 0.0045286] | 2 |
| 1 | 5 | `absolute` | `A_c7_only` | `xgboost_gpu` | `natural_coverage` | 0.0271606 | [0.021015, 0.033912] | 0.00451882 | 0.0211653 | 0.0320744 | 3 | 0.00296161 | [0.00067183, 0.0060591] | 2 |
| 1 | 5 | `absolute` | `A_c7_only` | `xgboost_gpu` | `stage1_common_matched` | 0.0271606 | [0.021015, 0.033912] | 0.00451882 | 0.0211653 | 0.0320744 | 3 | 0.00296161 | [0.00067183, 0.0060591] | 2 |
| 1 | 5 | `absolute` | `D_full_context` | `hist_gradient_boosting_cpu` | `natural_coverage` | 0.0468682 | [0.037386, 0.056256] | 0.0215072 | 0.0250732 | 0.0761388 | 3 | 0.00772791 | [0.0051256, 0.0094529] | 3 |
| 1 | 5 | `absolute` | `D_full_context` | `hist_gradient_boosting_cpu` | `stage1_common_matched` | 0.0468682 | [0.037386, 0.056256] | 0.0215072 | 0.0250732 | 0.0761388 | 3 | 0.00772791 | [0.0051256, 0.0094529] | 3 |
| 1 | 5 | `absolute` | `D_full_context` | `lightgbm_cpu` | `natural_coverage` | 0.0219955 | [0.014825, 0.028837] | 0.0107859 | 0.00755313 | 0.0334672 | 3 | -0.00170152 | [-0.003457, 0.00019458] | 1 |
| 1 | 5 | `absolute` | `D_full_context` | `lightgbm_cpu` | `stage1_common_matched` | 0.0219955 | [0.014825, 0.028837] | 0.0107859 | 0.00755313 | 0.0334672 | 3 | -0.00170152 | [-0.003457, 0.00019458] | 1 |
| 1 | 5 | `absolute` | `D_full_context` | `xgboost_gpu` | `natural_coverage` | 0.00451938 | [-0.0028515, 0.01013] | 0.00483763 | -0.00118761 | 0.0106404 | 2 | -0.00158479 | [-0.0032052, 0.00061773] | 2 |
| 1 | 5 | `absolute` | `D_full_context` | `xgboost_gpu` | `stage1_common_matched` | 0.00451938 | [-0.0028515, 0.01013] | 0.00483763 | -0.00118761 | 0.0106404 | 2 | -0.00158479 | [-0.0032052, 0.00061773] | 2 |
| 1 | 5 | `market_relative` | `A_c7_only` | `hist_gradient_boosting_cpu` | `natural_coverage` | 0.0547027 | [0.046542, 0.062793] | 0.0144821 | 0.0388117 | 0.0738377 | 3 | 0.0102258 | [0.0076742, 0.012513] | 3 |
| 1 | 5 | `market_relative` | `A_c7_only` | `hist_gradient_boosting_cpu` | `stage1_common_matched` | 0.0547027 | [0.046542, 0.062793] | 0.0144821 | 0.0388117 | 0.0738377 | 3 | 0.0102258 | [0.0076742, 0.012513] | 3 |
| 1 | 5 | `market_relative` | `A_c7_only` | `lightgbm_cpu` | `natural_coverage` | 0.0507703 | [0.041678, 0.058852] | 0.0115136 | 0.0361069 | 0.0642324 | 3 | 0.00854297 | [0.0063978, 0.011661] | 3 |
| 1 | 5 | `market_relative` | `A_c7_only` | `lightgbm_cpu` | `stage1_common_matched` | 0.0507703 | [0.041678, 0.058852] | 0.0115136 | 0.0361069 | 0.0642324 | 3 | 0.00854297 | [0.0063978, 0.011661] | 3 |
| 1 | 5 | `market_relative` | `A_c7_only` | `xgboost_gpu` | `natural_coverage` | 0.0403916 | [0.032835, 0.04808] | 0.00814042 | 0.0289077 | 0.0468324 | 3 | 0.00665142 | [0.0044315, 0.0096925] | 3 |
| 1 | 5 | `market_relative` | `A_c7_only` | `xgboost_gpu` | `stage1_common_matched` | 0.0403916 | [0.032835, 0.04808] | 0.00814042 | 0.0289077 | 0.0468324 | 3 | 0.00665142 | [0.0044315, 0.0096925] | 3 |
| 1 | 5 | `market_relative` | `B_market_context` | `hist_gradient_boosting_cpu` | `natural_coverage` | 0.0632429 | [0.055682, 0.071071] | 0.0188024 | 0.0480523 | 0.0897387 | 3 | 0.0102342 | [0.0077268, 0.012735] | 3 |
| 1 | 5 | `market_relative` | `B_market_context` | `hist_gradient_boosting_cpu` | `stage1_common_matched` | 0.0632429 | [0.055682, 0.071071] | 0.0188024 | 0.0480523 | 0.0897387 | 3 | 0.0102342 | [0.0077268, 0.012735] | 3 |
| 1 | 5 | `market_relative` | `B_market_context` | `lightgbm_cpu` | `natural_coverage` | 0.0442603 | [0.036072, 0.052613] | 0.024285 | 0.0118941 | 0.0703914 | 3 | 0.00811088 | [0.0054413, 0.010282] | 3 |
| 1 | 5 | `market_relative` | `B_market_context` | `lightgbm_cpu` | `stage1_common_matched` | 0.0442603 | [0.036072, 0.052613] | 0.024285 | 0.0118941 | 0.0703914 | 3 | 0.00811088 | [0.0054413, 0.010282] | 3 |
| 1 | 5 | `market_relative` | `B_market_context` | `xgboost_gpu` | `natural_coverage` | 0.0441284 | [0.03499, 0.054526] | 0.0264699 | 0.0100626 | 0.0746009 | 3 | 0.00385451 | [0.0016183, 0.0067297] | 2 |
| 1 | 5 | `market_relative` | `B_market_context` | `xgboost_gpu` | `stage1_common_matched` | 0.0441284 | [0.03499, 0.054526] | 0.0264699 | 0.0100626 | 0.0746009 | 3 | 0.00385451 | [0.0016183, 0.0067297] | 2 |
| 1 | 5 | `market_relative` | `D_full_context` | `hist_gradient_boosting_cpu` | `natural_coverage` | 0.0548819 | [0.047467, 0.063136] | 0.0173116 | 0.0336489 | 0.0760533 | 3 | 0.00783849 | [0.0053435, 0.010013] | 3 |
| 1 | 5 | `market_relative` | `D_full_context` | `hist_gradient_boosting_cpu` | `stage1_common_matched` | 0.0548819 | [0.047467, 0.063136] | 0.0173116 | 0.0336489 | 0.0760533 | 3 | 0.00783849 | [0.0053435, 0.010013] | 3 |
| 1 | 5 | `market_relative` | `D_full_context` | `lightgbm_cpu` | `natural_coverage` | 0.0407527 | [0.033003, 0.04916] | 0.0188707 | 0.017128 | 0.0633149 | 3 | 0.00548002 | [0.0030318, 0.0078167] | 3 |
| 1 | 5 | `market_relative` | `D_full_context` | `lightgbm_cpu` | `stage1_common_matched` | 0.0407527 | [0.033003, 0.04916] | 0.0188707 | 0.017128 | 0.0633149 | 3 | 0.00548002 | [0.0030318, 0.0078167] | 3 |
| 1 | 5 | `market_relative` | `D_full_context` | `xgboost_gpu` | `natural_coverage` | 0.040305 | [0.032509, 0.050087] | 0.0198613 | 0.0154727 | 0.0640888 | 3 | 0.00327789 | [0.001002, 0.0061713] | 2 |
| 1 | 5 | `market_relative` | `D_full_context` | `xgboost_gpu` | `stage1_common_matched` | 0.040305 | [0.032509, 0.050087] | 0.0198613 | 0.0154727 | 0.0640888 | 3 | 0.00327789 | [0.001002, 0.0061713] | 2 |
| 1 | 5 | `market_relative` | `E_context_only` | `hist_gradient_boosting_cpu` | `natural_coverage` | 0.0451221 | [0.03735, 0.052771] | 0.0155076 | 0.026301 | 0.0642822 | 3 | 0.00497449 | [0.0024479, 0.0072487] | 3 |
| 1 | 5 | `market_relative` | `E_context_only` | `hist_gradient_boosting_cpu` | `stage1_common_matched` | 0.0451221 | [0.03735, 0.052771] | 0.0155076 | 0.026301 | 0.0642822 | 3 | 0.00497449 | [0.0024479, 0.0072487] | 3 |
| 1 | 5 | `market_relative` | `E_context_only` | `lightgbm_cpu` | `natural_coverage` | 0.0377211 | [0.031054, 0.047295] | 0.0197176 | 0.022787 | 0.0655819 | 3 | 0.00449081 | [0.0019317, 0.0071621] | 3 |
| 1 | 5 | `market_relative` | `E_context_only` | `lightgbm_cpu` | `stage1_common_matched` | 0.0377211 | [0.031054, 0.047295] | 0.0197176 | 0.022787 | 0.0655819 | 3 | 0.00449081 | [0.0019317, 0.0071621] | 3 |
| 1 | 5 | `market_relative` | `E_context_only` | `xgboost_gpu` | `natural_coverage` | 0.0436228 | [0.035943, 0.05287] | 0.0135427 | 0.0254377 | 0.0579197 | 3 | 0.00612814 | [0.0039302, 0.0082942] | 3 |
| 1 | 5 | `market_relative` | `E_context_only` | `xgboost_gpu` | `stage1_common_matched` | 0.0436228 | [0.035943, 0.05287] | 0.0135427 | 0.0254377 | 0.0579197 | 3 | 0.00612814 | [0.0039302, 0.0082942] | 3 |
| 1 | 10 | `absolute` | `A_c7_only` | `hist_gradient_boosting_cpu` | `natural_coverage` | 0.045133 | [0.035977, 0.053063] | 0.0127396 | 0.0280843 | 0.0587022 | 3 | 0.0106314 | [0.0068406, 0.013276] | 3 |
| 1 | 10 | `absolute` | `A_c7_only` | `hist_gradient_boosting_cpu` | `stage1_common_matched` | 0.045133 | [0.035977, 0.053063] | 0.0127396 | 0.0280843 | 0.0587022 | 3 | 0.0106314 | [0.0068406, 0.013276] | 3 |
| 1 | 10 | `absolute` | `A_c7_only` | `lightgbm_cpu` | `natural_coverage` | 0.0385854 | [0.031716, 0.04884] | 0.0169172 | 0.020062 | 0.0609601 | 3 | 0.000895727 | [-0.0019447, 0.0047214] | 1 |
| 1 | 10 | `absolute` | `A_c7_only` | `lightgbm_cpu` | `stage1_common_matched` | 0.0385854 | [0.031716, 0.04884] | 0.0169172 | 0.020062 | 0.0609601 | 3 | 0.000895727 | [-0.0019447, 0.0047214] | 1 |
| 1 | 10 | `absolute` | `A_c7_only` | `xgboost_gpu` | `natural_coverage` | 0.0127495 | [0.0042316, 0.019695] | 0.0260921 | -0.0171886 | 0.0463995 | 2 | 0.00402924 | [0.00081182, 0.0082973] | 1 |
| 1 | 10 | `absolute` | `A_c7_only` | `xgboost_gpu` | `stage1_common_matched` | 0.0127495 | [0.0042316, 0.019695] | 0.0260921 | -0.0171886 | 0.0463995 | 2 | 0.00402924 | [0.00081182, 0.0082973] | 1 |
| 1 | 10 | `absolute` | `D_full_context` | `hist_gradient_boosting_cpu` | `natural_coverage` | 0.0445999 | [0.035108, 0.053502] | 0.0249372 | 0.0150781 | 0.0760683 | 3 | 0.0113721 | [0.0079285, 0.013918] | 3 |
| 1 | 10 | `absolute` | `D_full_context` | `hist_gradient_boosting_cpu` | `stage1_common_matched` | 0.0445999 | [0.035108, 0.053502] | 0.0249372 | 0.0150781 | 0.0760683 | 3 | 0.0113721 | [0.0079285, 0.013918] | 3 |
| 1 | 10 | `absolute` | `D_full_context` | `lightgbm_cpu` | `natural_coverage` | 0.00689004 | [-0.0016093, 0.0149] | 0.000442208 | 0.00641472 | 0.00747966 | 3 | -0.00263102 | [-0.0049521, 0.00077417] | 1 |
| 1 | 10 | `absolute` | `D_full_context` | `lightgbm_cpu` | `stage1_common_matched` | 0.00689004 | [-0.0016093, 0.0149] | 0.000442208 | 0.00641472 | 0.00747966 | 3 | -0.00263102 | [-0.0049521, 0.00077417] | 1 |
| 1 | 10 | `absolute` | `D_full_context` | `xgboost_gpu` | `natural_coverage` | 0.0168001 | [0.010123, 0.024209] | 0.0304475 | -0.0203398 | 0.0542392 | 2 | -0.00154061 | [-0.0040545, 0.001094] | 1 |
| 1 | 10 | `absolute` | `D_full_context` | `xgboost_gpu` | `stage1_common_matched` | 0.0168001 | [0.010123, 0.024209] | 0.0304475 | -0.0203398 | 0.0542392 | 2 | -0.00154061 | [-0.0040545, 0.001094] | 1 |
| 1 | 10 | `market_relative` | `A_c7_only` | `hist_gradient_boosting_cpu` | `natural_coverage` | 0.0349727 | [0.026653, 0.043063] | 0.01884 | 0.0208063 | 0.0615983 | 3 | 0.0147245 | [0.010766, 0.01818] | 3 |
| 1 | 10 | `market_relative` | `A_c7_only` | `hist_gradient_boosting_cpu` | `stage1_common_matched` | 0.0349727 | [0.026653, 0.043063] | 0.01884 | 0.0208063 | 0.0615983 | 3 | 0.0147245 | [0.010766, 0.01818] | 3 |
| 1 | 10 | `market_relative` | `A_c7_only` | `lightgbm_cpu` | `natural_coverage` | 0.0386869 | [0.031511, 0.047043] | 0.0212574 | 0.0223156 | 0.0687083 | 3 | 0.0161678 | [0.0126, 0.020098] | 3 |
| 1 | 10 | `market_relative` | `A_c7_only` | `lightgbm_cpu` | `stage1_common_matched` | 0.0386869 | [0.031511, 0.047043] | 0.0212574 | 0.0223156 | 0.0687083 | 3 | 0.0161678 | [0.0126, 0.020098] | 3 |
| 1 | 10 | `market_relative` | `A_c7_only` | `xgboost_gpu` | `natural_coverage` | 0.025925 | [0.018092, 0.033758] | 0.0120814 | 0.0169714 | 0.0430039 | 3 | 0.00724118 | [0.0031185, 0.010545] | 3 |
| 1 | 10 | `market_relative` | `A_c7_only` | `xgboost_gpu` | `stage1_common_matched` | 0.025925 | [0.018092, 0.033758] | 0.0120814 | 0.0169714 | 0.0430039 | 3 | 0.00724118 | [0.0031185, 0.010545] | 3 |
| 1 | 10 | `market_relative` | `B_market_context` | `hist_gradient_boosting_cpu` | `natural_coverage` | 0.0284957 | [0.02023, 0.036786] | 0.0285791 | 0.00405123 | 0.0685926 | 3 | 0.012261 | [0.0072963, 0.015415] | 2 |
| 1 | 10 | `market_relative` | `B_market_context` | `hist_gradient_boosting_cpu` | `stage1_common_matched` | 0.0284957 | [0.02023, 0.036786] | 0.0285791 | 0.00405123 | 0.0685926 | 3 | 0.012261 | [0.0072963, 0.015415] | 2 |
| 1 | 10 | `market_relative` | `B_market_context` | `lightgbm_cpu` | `natural_coverage` | 0.0178985 | [0.0096514, 0.027905] | 0.034821 | -0.0102871 | 0.0669618 | 1 | 0.00106799 | [-0.0023704, 0.0046332] | 1 |
| 1 | 10 | `market_relative` | `B_market_context` | `lightgbm_cpu` | `stage1_common_matched` | 0.0178985 | [0.0096514, 0.027905] | 0.034821 | -0.0102871 | 0.0669618 | 1 | 0.00106799 | [-0.0023704, 0.0046332] | 1 |
| 1 | 10 | `market_relative` | `B_market_context` | `xgboost_gpu` | `natural_coverage` | 0.0276873 | [0.020064, 0.036778] | 0.0258103 | 0.00471294 | 0.0637385 | 3 | 0.0123671 | [0.00739, 0.015362] | 3 |
| 1 | 10 | `market_relative` | `B_market_context` | `xgboost_gpu` | `stage1_common_matched` | 0.0276873 | [0.020064, 0.036778] | 0.0258103 | 0.00471294 | 0.0637385 | 3 | 0.0123671 | [0.00739, 0.015362] | 3 |
| 1 | 10 | `market_relative` | `D_full_context` | `hist_gradient_boosting_cpu` | `natural_coverage` | 0.0215464 | [0.01431, 0.030768] | 0.0311236 | -0.0148991 | 0.0611423 | 2 | 0.00523119 | [0.0010847, 0.0078906] | 2 |
| 1 | 10 | `market_relative` | `D_full_context` | `hist_gradient_boosting_cpu` | `stage1_common_matched` | 0.0215464 | [0.01431, 0.030768] | 0.0311236 | -0.0148991 | 0.0611423 | 2 | 0.00523119 | [0.0010847, 0.0078906] | 2 |
| 1 | 10 | `market_relative` | `D_full_context` | `lightgbm_cpu` | `natural_coverage` | 0.0304083 | [0.022042, 0.038417] | 0.0355745 | 0.00370869 | 0.0806859 | 3 | 0.00372644 | [0.0016596, 0.0067647] | 2 |
| 1 | 10 | `market_relative` | `D_full_context` | `lightgbm_cpu` | `stage1_common_matched` | 0.0304083 | [0.022042, 0.038417] | 0.0355745 | 0.00370869 | 0.0806859 | 3 | 0.00372644 | [0.0016596, 0.0067647] | 2 |
| 1 | 10 | `market_relative` | `D_full_context` | `xgboost_gpu` | `natural_coverage` | 0.0267224 | [0.019541, 0.036185] | 0.041696 | -0.00515088 | 0.085623 | 1 | 0.00741113 | [0.0036556, 0.011349] | 1 |
| 1 | 10 | `market_relative` | `D_full_context` | `xgboost_gpu` | `stage1_common_matched` | 0.0267224 | [0.019541, 0.036185] | 0.041696 | -0.00515088 | 0.085623 | 1 | 0.00741113 | [0.0036556, 0.011349] | 1 |
| 1 | 10 | `market_relative` | `E_context_only` | `hist_gradient_boosting_cpu` | `natural_coverage` | 0.022772 | [0.01501, 0.03138] | 0.0242032 | -0.00897388 | 0.0497282 | 2 | 0.00481079 | [0.0014564, 0.0085155] | 2 |
| 1 | 10 | `market_relative` | `E_context_only` | `hist_gradient_boosting_cpu` | `stage1_common_matched` | 0.022772 | [0.01501, 0.03138] | 0.0242032 | -0.00897388 | 0.0497282 | 2 | 0.00481079 | [0.0014564, 0.0085155] | 2 |
| 1 | 10 | `market_relative` | `E_context_only` | `lightgbm_cpu` | `natural_coverage` | 0.012939 | [0.0057859, 0.020774] | 0.0222753 | -0.00771698 | 0.0438651 | 2 | 0.00492673 | [0.00071274, 0.0076302] | 3 |
| 1 | 10 | `market_relative` | `E_context_only` | `lightgbm_cpu` | `stage1_common_matched` | 0.012939 | [0.0057859, 0.020774] | 0.0222753 | -0.00771698 | 0.0438651 | 2 | 0.00492673 | [0.00071274, 0.0076302] | 3 |
| 1 | 10 | `market_relative` | `E_context_only` | `xgboost_gpu` | `natural_coverage` | 0.0137838 | [0.0064686, 0.022103] | 0.0345233 | -0.0146634 | 0.0623709 | 1 | 0.00546128 | [0.0018232, 0.0084128] | 2 |
| 1 | 10 | `market_relative` | `E_context_only` | `xgboost_gpu` | `stage1_common_matched` | 0.0137838 | [0.0064686, 0.022103] | 0.0345233 | -0.0146634 | 0.0623709 | 1 | 0.00546128 | [0.0018232, 0.0084128] | 2 |
| 2 | 5 | `sector_relaxed_3_peer` | `A_c7_only` | `lightgbm_cpu` | `natural_coverage` | 0.0372601 | [0.0306, 0.042933] | 0.00152842 | 0.0351646 | 0.0387671 | 3 | 0.00870424 | [0.0066366, 0.011282] | 3 |
| 2 | 5 | `sector_relaxed_3_peer` | `A_c7_only` | `lightgbm_cpu` | `strict_5_peer_matched` | 0.037821 | [0.031533, 0.044625] | 0.00208077 | 0.0349057 | 0.0396249 | 3 | 0.00727899 | [0.0051292, 0.010102] | 3 |
| 2 | 5 | `sector_relaxed_3_peer` | `A_c7_only` | `xgboost_gpu` | `natural_coverage` | 0.0418593 | [0.036091, 0.048628] | 0.00235067 | 0.0385356 | 0.0435806 | 3 | 0.00952774 | [0.0073001, 0.012141] | 3 |
| 2 | 5 | `sector_relaxed_3_peer` | `A_c7_only` | `xgboost_gpu` | `strict_5_peer_matched` | 0.0425728 | [0.036152, 0.049864] | 0.00343613 | 0.0390772 | 0.0472439 | 3 | 0.00859228 | [0.0061923, 0.010732] | 3 |
| 2 | 5 | `sector_relaxed_3_peer` | `C_sector_context` | `lightgbm_cpu` | `natural_coverage` | 0.0403025 | [0.033923, 0.047611] | 0.00227416 | 0.0371487 | 0.0424254 | 3 | 0.00844563 | [0.0055921, 0.010317] | 3 |
| 2 | 5 | `sector_relaxed_3_peer` | `C_sector_context` | `lightgbm_cpu` | `strict_5_peer_matched` | 0.0376892 | [0.030592, 0.045184] | 0.00597513 | 0.0314002 | 0.0457214 | 3 | 0.00607377 | [0.0034054, 0.0083494] | 3 |
| 2 | 5 | `sector_relaxed_3_peer` | `C_sector_context` | `xgboost_gpu` | `natural_coverage` | 0.0344536 | [0.028308, 0.04129] | 0.00392049 | 0.0297716 | 0.0393664 | 3 | 0.00679187 | [0.0039753, 0.0086831] | 3 |
| 2 | 5 | `sector_relaxed_3_peer` | `C_sector_context` | `xgboost_gpu` | `strict_5_peer_matched` | 0.0330693 | [0.025673, 0.040753] | 0.00615257 | 0.0281265 | 0.0417422 | 3 | 0.00537128 | [0.0028727, 0.0074388] | 3 |
| 2 | 5 | `sector_relaxed_3_peer` | `D_full_context` | `lightgbm_cpu` | `natural_coverage` | 0.0333765 | [0.027754, 0.039762] | 0.00729253 | 0.0278475 | 0.0436805 | 3 | 0.00564984 | [0.0025033, 0.0073541] | 3 |
| 2 | 5 | `sector_relaxed_3_peer` | `D_full_context` | `lightgbm_cpu` | `strict_5_peer_matched` | 0.0312412 | [0.025127, 0.03803] | 0.00661444 | 0.0249924 | 0.0403939 | 3 | 0.0059355 | [0.0031179, 0.0079132] | 3 |
| 2 | 5 | `sector_relaxed_3_peer` | `D_full_context` | `xgboost_gpu` | `natural_coverage` | 0.0362676 | [0.030641, 0.042299] | 0.00537051 | 0.0286974 | 0.0405841 | 3 | 0.00713303 | [0.0036408, 0.008703] | 3 |
| 2 | 5 | `sector_relaxed_3_peer` | `D_full_context` | `xgboost_gpu` | `strict_5_peer_matched` | 0.0340171 | [0.02766, 0.04122] | 0.0039955 | 0.0284846 | 0.0377781 | 3 | 0.00686205 | [0.0034576, 0.0083729] | 3 |
| 2 | 5 | `sector_shrunk_3_peer` | `A_c7_only` | `lightgbm_cpu` | `natural_coverage` | 0.0412374 | [0.0344, 0.048866] | 0.00770427 | 0.0337211 | 0.0518265 | 3 | 0.00984709 | [0.0077826, 0.012229] | 3 |
| 2 | 5 | `sector_shrunk_3_peer` | `A_c7_only` | `lightgbm_cpu` | `strict_5_peer_matched` | 0.0423277 | [0.035546, 0.050609] | 0.00731119 | 0.0362014 | 0.0526042 | 3 | 0.0089907 | [0.0071537, 0.011617] | 3 |
| 2 | 5 | `sector_shrunk_3_peer` | `A_c7_only` | `xgboost_gpu` | `natural_coverage` | 0.0427311 | [0.035344, 0.049613] | 0.011939 | 0.02819 | 0.0574331 | 3 | 0.00910721 | [0.0070915, 0.011173] | 3 |
| 2 | 5 | `sector_shrunk_3_peer` | `A_c7_only` | `xgboost_gpu` | `strict_5_peer_matched` | 0.0457315 | [0.03879, 0.053316] | 0.0105884 | 0.0333285 | 0.0591991 | 3 | 0.00928883 | [0.0070677, 0.011132] | 3 |
| 2 | 5 | `sector_shrunk_3_peer` | `C_sector_context` | `lightgbm_cpu` | `natural_coverage` | 0.0485837 | [0.041007, 0.056225] | 0.00807761 | 0.0380869 | 0.0577353 | 3 | 0.009927 | [0.0071704, 0.011923] | 3 |
| 2 | 5 | `sector_shrunk_3_peer` | `C_sector_context` | `lightgbm_cpu` | `strict_5_peer_matched` | 0.0444205 | [0.036451, 0.051817] | 0.0100391 | 0.0302937 | 0.052709 | 3 | 0.00828808 | [0.0056503, 0.0099304] | 3 |
| 2 | 5 | `sector_shrunk_3_peer` | `C_sector_context` | `xgboost_gpu` | `natural_coverage` | 0.0394163 | [0.032097, 0.046444] | 0.00832976 | 0.0276465 | 0.0457275 | 3 | 0.00604243 | [0.0029975, 0.0082398] | 3 |
| 2 | 5 | `sector_shrunk_3_peer` | `C_sector_context` | `xgboost_gpu` | `strict_5_peer_matched` | 0.036974 | [0.029373, 0.044899] | 0.0102153 | 0.0233253 | 0.0478987 | 3 | 0.0049733 | [0.0019052, 0.0069611] | 3 |
| 2 | 5 | `sector_shrunk_3_peer` | `D_full_context` | `lightgbm_cpu` | `natural_coverage` | 0.0459278 | [0.03741, 0.054188] | 0.00400267 | 0.0407773 | 0.0505369 | 3 | 0.00940245 | [0.0065262, 0.011357] | 3 |
| 2 | 5 | `sector_shrunk_3_peer` | `D_full_context` | `lightgbm_cpu` | `strict_5_peer_matched` | 0.0412183 | [0.032543, 0.049238] | 0.00409953 | 0.0368544 | 0.0467058 | 3 | 0.0089722 | [0.0060707, 0.011013] | 3 |
| 2 | 5 | `sector_shrunk_3_peer` | `D_full_context` | `xgboost_gpu` | `natural_coverage` | 0.0443973 | [0.037536, 0.052326] | 0.0110227 | 0.0290959 | 0.0546268 | 3 | 0.00886892 | [0.0056697, 0.010945] | 3 |
| 2 | 5 | `sector_shrunk_3_peer` | `D_full_context` | `xgboost_gpu` | `strict_5_peer_matched` | 0.039647 | [0.03188, 0.047968] | 0.0125916 | 0.0226069 | 0.0526447 | 3 | 0.00967255 | [0.006624, 0.011967] | 3 |
| 2 | 5 | `sector_strict_5_peer` | `A_c7_only` | `lightgbm_cpu` | `natural_coverage` | 0.0329604 | [0.026134, 0.039687] | 0.0103214 | 0.0210066 | 0.0461917 | 3 | 0.00888512 | [0.0059945, 0.010728] | 3 |
| 2 | 5 | `sector_strict_5_peer` | `A_c7_only` | `lightgbm_cpu` | `strict_5_peer_matched` | 0.0329604 | [0.026134, 0.039687] | 0.0103214 | 0.0210066 | 0.0461917 | 3 | 0.00888512 | [0.0059945, 0.010728] | 3 |
| 2 | 5 | `sector_strict_5_peer` | `A_c7_only` | `xgboost_gpu` | `natural_coverage` | 0.033968 | [0.026863, 0.041566] | 0.00914745 | 0.0213511 | 0.0427513 | 3 | 0.0101921 | [0.0072655, 0.011799] | 3 |
| 2 | 5 | `sector_strict_5_peer` | `A_c7_only` | `xgboost_gpu` | `strict_5_peer_matched` | 0.033968 | [0.026863, 0.041566] | 0.00914745 | 0.0213511 | 0.0427513 | 3 | 0.0101921 | [0.0072655, 0.011799] | 3 |
| 2 | 5 | `sector_strict_5_peer` | `C_sector_context` | `lightgbm_cpu` | `natural_coverage` | 0.0301346 | [0.023756, 0.037477] | 0.010486 | 0.0203971 | 0.0446895 | 3 | 0.00567901 | [0.0029776, 0.0076536] | 3 |
| 2 | 5 | `sector_strict_5_peer` | `C_sector_context` | `lightgbm_cpu` | `strict_5_peer_matched` | 0.0301346 | [0.023756, 0.037477] | 0.010486 | 0.0203971 | 0.0446895 | 3 | 0.00567901 | [0.0029776, 0.0076536] | 3 |
| 2 | 5 | `sector_strict_5_peer` | `C_sector_context` | `xgboost_gpu` | `natural_coverage` | 0.0334987 | [0.026179, 0.041401] | 0.00896202 | 0.0208351 | 0.0402782 | 3 | 0.0061417 | [0.0030381, 0.0078682] | 3 |
| 2 | 5 | `sector_strict_5_peer` | `C_sector_context` | `xgboost_gpu` | `strict_5_peer_matched` | 0.0334987 | [0.026179, 0.041401] | 0.00896202 | 0.0208351 | 0.0402782 | 3 | 0.0061417 | [0.0030381, 0.0078682] | 3 |
| 2 | 5 | `sector_strict_5_peer` | `D_full_context` | `lightgbm_cpu` | `natural_coverage` | 0.0433724 | [0.036208, 0.051369] | 0.0207828 | 0.01513 | 0.064541 | 3 | 0.0106708 | [0.0074066, 0.012286] | 3 |
| 2 | 5 | `sector_strict_5_peer` | `D_full_context` | `lightgbm_cpu` | `strict_5_peer_matched` | 0.0433724 | [0.036208, 0.051369] | 0.0207828 | 0.01513 | 0.064541 | 3 | 0.0106708 | [0.0074066, 0.012286] | 3 |
| 2 | 5 | `sector_strict_5_peer` | `D_full_context` | `xgboost_gpu` | `natural_coverage` | 0.0403391 | [0.033258, 0.048195] | 0.0136364 | 0.0229649 | 0.0562739 | 3 | 0.00854855 | [0.0055925, 0.010167] | 3 |
| 2 | 5 | `sector_strict_5_peer` | `D_full_context` | `xgboost_gpu` | `strict_5_peer_matched` | 0.0403391 | [0.033258, 0.048195] | 0.0136364 | 0.0229649 | 0.0562739 | 3 | 0.00854855 | [0.0055925, 0.010167] | 3 |
| 2 | 10 | `sector_relaxed_3_peer` | `A_c7_only` | `lightgbm_cpu` | `natural_coverage` | 0.0265817 | [0.018823, 0.033308] | 0.0192747 | 0.0094207 | 0.0535033 | 3 | 0.0127745 | [0.0083243, 0.015266] | 3 |
| 2 | 10 | `sector_relaxed_3_peer` | `A_c7_only` | `lightgbm_cpu` | `strict_5_peer_matched` | 0.024295 | [0.016309, 0.032416] | 0.0197899 | 0.0100788 | 0.0522809 | 3 | 0.0105718 | [0.0057087, 0.012956] | 3 |
| 2 | 10 | `sector_relaxed_3_peer` | `A_c7_only` | `xgboost_gpu` | `natural_coverage` | 0.0272995 | [0.020084, 0.034525] | 0.0221961 | 0.0069453 | 0.0581715 | 3 | 0.013238 | [0.0087834, 0.016699] | 3 |
| 2 | 10 | `sector_relaxed_3_peer` | `A_c7_only` | `xgboost_gpu` | `strict_5_peer_matched` | 0.0241436 | [0.015905, 0.032679] | 0.0228849 | 0.00621245 | 0.0564423 | 3 | 0.00909308 | [0.0046997, 0.011679] | 3 |
| 2 | 10 | `sector_relaxed_3_peer` | `C_sector_context` | `lightgbm_cpu` | `natural_coverage` | 0.0298336 | [0.022619, 0.036004] | 0.0150325 | 0.0179474 | 0.0510411 | 3 | 0.0087314 | [0.0032934, 0.011795] | 2 |
| 2 | 10 | `sector_relaxed_3_peer` | `C_sector_context` | `lightgbm_cpu` | `strict_5_peer_matched` | 0.0272063 | [0.019125, 0.034338] | 0.0195243 | 0.00905 | 0.0543 | 3 | 0.00984901 | [0.00556, 0.012072] | 3 |
| 2 | 10 | `sector_relaxed_3_peer` | `C_sector_context` | `xgboost_gpu` | `natural_coverage` | 0.0269379 | [0.020549, 0.033786] | 0.00550859 | 0.0218554 | 0.0345921 | 3 | 0.0143643 | [0.0095277, 0.016654] | 3 |
| 2 | 10 | `sector_relaxed_3_peer` | `C_sector_context` | `xgboost_gpu` | `strict_5_peer_matched` | 0.0218899 | [0.013553, 0.030277] | 0.00938388 | 0.0118077 | 0.0344041 | 3 | 0.00794476 | [0.0031855, 0.0095457] | 3 |
| 2 | 10 | `sector_relaxed_3_peer` | `D_full_context` | `lightgbm_cpu` | `natural_coverage` | 0.0229883 | [0.016908, 0.029505] | 0.0120271 | 0.00839959 | 0.037856 | 3 | 0.00429554 | [0.00024388, 0.0068334] | 3 |
| 2 | 10 | `sector_relaxed_3_peer` | `D_full_context` | `lightgbm_cpu` | `strict_5_peer_matched` | 0.0248529 | [0.018176, 0.031913] | 0.0156966 | 0.0101463 | 0.0466062 | 3 | 0.00768948 | [0.0042573, 0.010067] | 3 |
| 2 | 10 | `sector_relaxed_3_peer` | `D_full_context` | `xgboost_gpu` | `natural_coverage` | 0.0306495 | [0.023998, 0.035716] | 0.00505051 | 0.0248008 | 0.0371244 | 3 | 0.0143963 | [0.010343, 0.016984] | 3 |
| 2 | 10 | `sector_relaxed_3_peer` | `D_full_context` | `xgboost_gpu` | `strict_5_peer_matched` | 0.0274234 | [0.019414, 0.034264] | 0.00264537 | 0.023784 | 0.0299934 | 3 | 0.0112537 | [0.0077024, 0.01379] | 3 |
| 2 | 10 | `sector_shrunk_3_peer` | `A_c7_only` | `lightgbm_cpu` | `natural_coverage` | 0.0324266 | [0.024238, 0.039478] | 0.0187677 | 0.0186326 | 0.0589611 | 3 | 0.0180146 | [0.013137, 0.020948] | 3 |
| 2 | 10 | `sector_shrunk_3_peer` | `A_c7_only` | `lightgbm_cpu` | `strict_5_peer_matched` | 0.0349624 | [0.026101, 0.042365] | 0.0150757 | 0.0233649 | 0.0562543 | 3 | 0.0166217 | [0.012334, 0.018511] | 3 |
| 2 | 10 | `sector_shrunk_3_peer` | `A_c7_only` | `xgboost_gpu` | `natural_coverage` | 0.0262196 | [0.018708, 0.033193] | 0.0318618 | -0.0096182 | 0.0677922 | 2 | 0.0129505 | [0.0085479, 0.015811] | 3 |
| 2 | 10 | `sector_shrunk_3_peer` | `A_c7_only` | `xgboost_gpu` | `strict_5_peer_matched` | 0.0271449 | [0.01968, 0.035553] | 0.0286394 | -0.00449052 | 0.0648653 | 2 | 0.0102664 | [0.0060078, 0.012443] | 3 |
| 2 | 10 | `sector_shrunk_3_peer` | `C_sector_context` | `lightgbm_cpu` | `natural_coverage` | 0.0288136 | [0.019979, 0.035539] | 0.0203052 | 0.00881113 | 0.0566581 | 3 | 0.0132278 | [0.0096133, 0.016209] | 3 |
| 2 | 10 | `sector_shrunk_3_peer` | `C_sector_context` | `lightgbm_cpu` | `strict_5_peer_matched` | 0.0252253 | [0.015716, 0.033225] | 0.0192355 | 0.00761584 | 0.0519866 | 3 | 0.00904857 | [0.0048219, 0.011519] | 3 |
| 2 | 10 | `sector_shrunk_3_peer` | `C_sector_context` | `xgboost_gpu` | `natural_coverage` | 0.0227586 | [0.015233, 0.029284] | 0.0137822 | 0.01012 | 0.0419279 | 3 | 0.00939003 | [0.005651, 0.011924] | 3 |
| 2 | 10 | `sector_shrunk_3_peer` | `C_sector_context` | `xgboost_gpu` | `strict_5_peer_matched` | 0.0215161 | [0.012833, 0.028109] | 0.0110048 | 0.0119529 | 0.0369309 | 3 | 0.00563038 | [0.0020338, 0.0085485] | 3 |
| 2 | 10 | `sector_shrunk_3_peer` | `D_full_context` | `lightgbm_cpu` | `natural_coverage` | 0.0332165 | [0.025424, 0.041004] | 0.0284538 | 0.00236301 | 0.0710145 | 3 | 0.015895 | [0.011808, 0.018781] | 3 |
| 2 | 10 | `sector_shrunk_3_peer` | `D_full_context` | `lightgbm_cpu` | `strict_5_peer_matched` | 0.0309718 | [0.021882, 0.038438] | 0.0297622 | -0.00112852 | 0.0705987 | 2 | 0.0144774 | [0.010581, 0.016555] | 3 |
| 2 | 10 | `sector_shrunk_3_peer` | `D_full_context` | `xgboost_gpu` | `natural_coverage` | 0.0425199 | [0.035247, 0.049339] | 0.0227738 | 0.0152985 | 0.0710376 | 3 | 0.0163316 | [0.012525, 0.019236] | 3 |
| 2 | 10 | `sector_shrunk_3_peer` | `D_full_context` | `xgboost_gpu` | `strict_5_peer_matched` | 0.0391815 | [0.031572, 0.046761] | 0.0244904 | 0.0114247 | 0.0709997 | 3 | 0.0130208 | [0.0087299, 0.015571] | 3 |
| 2 | 10 | `sector_strict_5_peer` | `A_c7_only` | `lightgbm_cpu` | `natural_coverage` | 0.0105156 | [0.0040527, 0.018199] | 0.00574072 | 0.00251723 | 0.0157205 | 3 | 0.00286213 | [-0.0013674, 0.0057337] | 1 |
| 2 | 10 | `sector_strict_5_peer` | `A_c7_only` | `lightgbm_cpu` | `strict_5_peer_matched` | 0.0105156 | [0.0040527, 0.018199] | 0.00574072 | 0.00251723 | 0.0157205 | 3 | 0.00286213 | [-0.0013674, 0.0057337] | 1 |
| 2 | 10 | `sector_strict_5_peer` | `A_c7_only` | `xgboost_gpu` | `natural_coverage` | 0.00732061 | [0.00031667, 0.015514] | 0.018392 | -0.0121302 | 0.0320008 | 2 | 0.0105295 | [0.0063365, 0.012851] | 2 |
| 2 | 10 | `sector_strict_5_peer` | `A_c7_only` | `xgboost_gpu` | `strict_5_peer_matched` | 0.00732061 | [0.00031667, 0.015514] | 0.018392 | -0.0121302 | 0.0320008 | 2 | 0.0105295 | [0.0063365, 0.012851] | 2 |
| 2 | 10 | `sector_strict_5_peer` | `C_sector_context` | `lightgbm_cpu` | `natural_coverage` | 0.0180041 | [0.010366, 0.025104] | 0.013031 | 0.00593044 | 0.0360983 | 3 | -0.000711709 | [-0.0045671, 0.0013265] | 1 |
| 2 | 10 | `sector_strict_5_peer` | `C_sector_context` | `lightgbm_cpu` | `strict_5_peer_matched` | 0.0180041 | [0.010366, 0.025104] | 0.013031 | 0.00593044 | 0.0360983 | 3 | -0.000711709 | [-0.0045671, 0.0013265] | 1 |
| 2 | 10 | `sector_strict_5_peer` | `C_sector_context` | `xgboost_gpu` | `natural_coverage` | 0.0177077 | [0.0097367, 0.025721] | 0.00689443 | 0.0107227 | 0.0270915 | 3 | 0.0045841 | [0.00036507, 0.0066742] | 3 |
| 2 | 10 | `sector_strict_5_peer` | `C_sector_context` | `xgboost_gpu` | `strict_5_peer_matched` | 0.0177077 | [0.0097367, 0.025721] | 0.00689443 | 0.0107227 | 0.0270915 | 3 | 0.0045841 | [0.00036507, 0.0066742] | 3 |
| 2 | 10 | `sector_strict_5_peer` | `D_full_context` | `lightgbm_cpu` | `natural_coverage` | 0.0366803 | [0.028633, 0.044342] | 0.0220605 | 0.0169452 | 0.0674737 | 3 | 0.0135349 | [0.0084251, 0.015969] | 3 |
| 2 | 10 | `sector_strict_5_peer` | `D_full_context` | `lightgbm_cpu` | `strict_5_peer_matched` | 0.0366803 | [0.028633, 0.044342] | 0.0220605 | 0.0169452 | 0.0674737 | 3 | 0.0135349 | [0.0084251, 0.015969] | 3 |
| 2 | 10 | `sector_strict_5_peer` | `D_full_context` | `xgboost_gpu` | `natural_coverage` | 0.0236344 | [0.01606, 0.030552] | 0.0101149 | 0.0135026 | 0.0374454 | 3 | 0.00709345 | [0.003902, 0.010189] | 3 |
| 2 | 10 | `sector_strict_5_peer` | `D_full_context` | `xgboost_gpu` | `strict_5_peer_matched` | 0.0236344 | [0.01606, 0.030552] | 0.0101149 | 0.0135026 | 0.0374454 | 3 | 0.00709345 | [0.003902, 0.010189] | 3 |

## Training diagnostics

Fits: **216**; one-round fits: **22**; near-constant predictions: **0**; minimum prediction standard deviation: **0.0001103066**.

Selected rounds, prediction distributions, inner scores, devices, and runtime are available in the structured training diagnostics artifact.

## Six newly covered sectors — focused shrunk-target diagnostics

| Horizon | Features | Model | Fold | Sector | Rows | Mean daily IC | Spearman |
|---:|---|---|---|---|---:|---:|---:|
| 5 | `C_sector_context` | `lightgbm_cpu` | `fold_2023` | FERTILIZER | 626 | — | 0.0573988 |
| 5 | `C_sector_context` | `lightgbm_cpu` | `fold_2023` | OIL & GAS EXPLORATION COMPANIES | 984 | — | 0.0940033 |
| 5 | `C_sector_context` | `lightgbm_cpu` | `fold_2023` | REFINERY | 984 | — | 0.0451491 |
| 5 | `C_sector_context` | `xgboost_gpu` | `fold_2023` | FERTILIZER | 626 | — | 0.0784885 |
| 5 | `C_sector_context` | `xgboost_gpu` | `fold_2023` | OIL & GAS EXPLORATION COMPANIES | 984 | — | 0.0488492 |
| 5 | `C_sector_context` | `xgboost_gpu` | `fold_2023` | REFINERY | 984 | — | 0.0366144 |
| 5 | `C_sector_context` | `lightgbm_cpu` | `fold_2024` | FERTILIZER | 1199 | — | 0.0849555 |
| 5 | `C_sector_context` | `lightgbm_cpu` | `fold_2024` | OIL & GAS EXPLORATION COMPANIES | 984 | — | 0.0318013 |
| 5 | `C_sector_context` | `lightgbm_cpu` | `fold_2024` | REFINERY | 984 | — | 0.0127284 |
| 5 | `C_sector_context` | `lightgbm_cpu` | `fold_2024` | TRANSPORT | 532 | — | 0.202237 |
| 5 | `C_sector_context` | `xgboost_gpu` | `fold_2024` | FERTILIZER | 1199 | — | 0.0979426 |
| 5 | `C_sector_context` | `xgboost_gpu` | `fold_2024` | OIL & GAS EXPLORATION COMPANIES | 984 | — | 0.0473717 |
| 5 | `C_sector_context` | `xgboost_gpu` | `fold_2024` | REFINERY | 984 | — | 0.0132241 |
| 5 | `C_sector_context` | `xgboost_gpu` | `fold_2024` | TRANSPORT | 532 | — | 0.232762 |
| 5 | `C_sector_context` | `lightgbm_cpu` | `fold_2025` | FERTILIZER | 1243 | — | 0.0862916 |
| 5 | `C_sector_context` | `lightgbm_cpu` | `fold_2025` | LEATHER & TANNERIES | 176 | — | 0.200694 |
| 5 | `C_sector_context` | `lightgbm_cpu` | `fold_2025` | OIL & GAS EXPLORATION COMPANIES | 1000 | — | -0.0158722 |
| 5 | `C_sector_context` | `lightgbm_cpu` | `fold_2025` | PROPERTY | 68 | — | 0.331057 |
| 5 | `C_sector_context` | `lightgbm_cpu` | `fold_2025` | REFINERY | 1000 | — | 0.0213868 |
| 5 | `C_sector_context` | `lightgbm_cpu` | `fold_2025` | TRANSPORT | 1000 | — | 0.169808 |
| 5 | `C_sector_context` | `xgboost_gpu` | `fold_2025` | FERTILIZER | 1243 | — | 0.109351 |
| 5 | `C_sector_context` | `xgboost_gpu` | `fold_2025` | LEATHER & TANNERIES | 176 | — | 0.171194 |
| 5 | `C_sector_context` | `xgboost_gpu` | `fold_2025` | OIL & GAS EXPLORATION COMPANIES | 1000 | — | -0.0346028 |
| 5 | `C_sector_context` | `xgboost_gpu` | `fold_2025` | PROPERTY | 68 | — | 0.411547 |
| 5 | `C_sector_context` | `xgboost_gpu` | `fold_2025` | REFINERY | 1000 | — | 0.0398199 |
| 5 | `C_sector_context` | `xgboost_gpu` | `fold_2025` | TRANSPORT | 1000 | — | 0.0745517 |
| 10 | `A_c7_only` | `lightgbm_cpu` | `fold_2023` | FERTILIZER | 626 | — | 0.00305919 |
| 10 | `A_c7_only` | `lightgbm_cpu` | `fold_2023` | OIL & GAS EXPLORATION COMPANIES | 984 | — | 0.0181277 |
| 10 | `A_c7_only` | `lightgbm_cpu` | `fold_2023` | REFINERY | 984 | — | 0.0547863 |
| 10 | `A_c7_only` | `xgboost_gpu` | `fold_2023` | FERTILIZER | 626 | — | -0.0871012 |
| 10 | `A_c7_only` | `xgboost_gpu` | `fold_2023` | OIL & GAS EXPLORATION COMPANIES | 984 | — | 0.0436329 |
| 10 | `A_c7_only` | `xgboost_gpu` | `fold_2023` | REFINERY | 984 | — | -0.0785906 |
| 10 | `A_c7_only` | `lightgbm_cpu` | `fold_2024` | FERTILIZER | 1199 | — | -0.034349 |
| 10 | `A_c7_only` | `lightgbm_cpu` | `fold_2024` | OIL & GAS EXPLORATION COMPANIES | 984 | — | -0.0725667 |
| 10 | `A_c7_only` | `lightgbm_cpu` | `fold_2024` | REFINERY | 984 | — | 0.10687 |
| 10 | `A_c7_only` | `lightgbm_cpu` | `fold_2024` | TRANSPORT | 532 | — | 0.123481 |
| 10 | `A_c7_only` | `xgboost_gpu` | `fold_2024` | FERTILIZER | 1199 | — | 0.0189273 |
| 10 | `A_c7_only` | `xgboost_gpu` | `fold_2024` | OIL & GAS EXPLORATION COMPANIES | 984 | — | 0.054608 |
| 10 | `A_c7_only` | `xgboost_gpu` | `fold_2024` | REFINERY | 984 | — | 0.0873087 |
| 10 | `A_c7_only` | `xgboost_gpu` | `fold_2024` | TRANSPORT | 532 | — | 0.17669 |
| 10 | `A_c7_only` | `lightgbm_cpu` | `fold_2025` | FERTILIZER | 1243 | — | 0.168036 |
| 10 | `A_c7_only` | `lightgbm_cpu` | `fold_2025` | LEATHER & TANNERIES | 176 | — | -0.0137441 |
| 10 | `A_c7_only` | `lightgbm_cpu` | `fold_2025` | OIL & GAS EXPLORATION COMPANIES | 1000 | — | 0.105625 |
| 10 | `A_c7_only` | `lightgbm_cpu` | `fold_2025` | PROPERTY | 68 | — | 0.321746 |
| 10 | `A_c7_only` | `lightgbm_cpu` | `fold_2025` | REFINERY | 1000 | — | 0.0253406 |
| 10 | `A_c7_only` | `lightgbm_cpu` | `fold_2025` | TRANSPORT | 1000 | — | 0.268752 |
| 10 | `A_c7_only` | `xgboost_gpu` | `fold_2025` | FERTILIZER | 1243 | — | 0.170092 |
| 10 | `A_c7_only` | `xgboost_gpu` | `fold_2025` | LEATHER & TANNERIES | 176 | — | 0.043702 |
| 10 | `A_c7_only` | `xgboost_gpu` | `fold_2025` | OIL & GAS EXPLORATION COMPANIES | 1000 | — | 0.0847915 |
| 10 | `A_c7_only` | `xgboost_gpu` | `fold_2025` | PROPERTY | 68 | — | 0.514015 |
| 10 | `A_c7_only` | `xgboost_gpu` | `fold_2025` | REFINERY | 1000 | — | 0.0606343 |
| 10 | `A_c7_only` | `xgboost_gpu` | `fold_2025` | TRANSPORT | 1000 | — | 0.212521 |

## Interpretation guardrails

Natural-coverage sector results are always paired with strict-five-peer matched results. No result is called better solely because coverage or target variance changed. Sector, peer-tier, and training-period market-regime metrics are available in the structured subgroup artifact. The 2026 final holdout remained locked.

## Feature-importance fold stability

Mean pairwise gain-rank correlation is reported below. Higher is more stable; negative values indicate fold reversal.

| Source | Horizon | Target | Features | Mean pairwise rank correlation | Minimum |
|---|---:|---|---|---:|---:|
| C7 | 5 | absolute | A | 0.7078244275549436 | 0.6330723982670322 |
| C7 | 10 | absolute | A | 0.5381160491834723 | 0.34636568152532093 |
| C8 | 5 | market_relative | A_c7_only | 0.8326850007312298 | 0.7559006211180125 |
| C8 | 10 | market_relative | A_c7_only | 0.7261699426564224 | 0.6361839654394096 |
| C8 | 5 | sector_shrunk_3_peer | C_sector_context | 0.8009962285193034 | 0.7013496922206827 |
| C8 | 10 | sector_shrunk_3_peer | C_sector_context | 0.7411847345327836 | 0.6502910974781589 |
