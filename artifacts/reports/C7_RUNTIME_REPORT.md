# C7 Runtime Report

Canonical CPU mode uses one thread; XGBoost verification uses CUDA on `NVIDIA GeForce RTX 5070 Laptop GPU`.

## Fit and prediction runtime

| Task | Fold | Model | Device | Fit s | Predict s | Rounds | Train rows | Validation rows |
|---|---|---|---|---:|---:|---:|---:|---:|
| `fwd_open_to_close_ret_5s_adj` | `fold_2023` | `lightgbm_cpu` | `cpu` | 0.2630 | 0.0027 | 4 | 112787 | 35317 |
| `fwd_open_to_close_ret_5s_adj` | `fold_2023` | `hist_gradient_boosting_cpu` | `cpu` | 1.9928 | 0.0107 | 150 | 112787 | 35317 |
| `fwd_open_to_close_ret_5s_adj` | `fold_2023` | `xgboost_gpu` | `cuda` | 0.3076 | 0.0096 | 3 | 112787 | 35317 |
| `fwd_open_to_close_ret_5s_adj` | `fold_2024` | `lightgbm_cpu` | `cpu` | 1.0246 | 0.0551 | 129 | 146793 | 48505 |
| `fwd_open_to_close_ret_5s_adj` | `fold_2024` | `hist_gradient_boosting_cpu` | `cpu` | 0.4985 | 0.0139 | 150 | 146793 | 48505 |
| `fwd_open_to_close_ret_5s_adj` | `fold_2024` | `xgboost_gpu` | `cuda` | 0.6116 | 0.0162 | 78 | 146793 | 48505 |
| `fwd_open_to_close_ret_5s_adj` | `fold_2025` | `lightgbm_cpu` | `cpu` | 0.4571 | 0.0035 | 1 | 194556 | 64191 |
| `fwd_open_to_close_ret_5s_adj` | `fold_2025` | `hist_gradient_boosting_cpu` | `cpu` | 0.6401 | 0.0190 | 150 | 194556 | 64191 |
| `fwd_open_to_close_ret_5s_adj` | `fold_2025` | `xgboost_gpu` | `cuda` | 0.4936 | 0.0235 | 2 | 194556 | 64191 |
| `fwd_open_to_close_ret_10s_adj` | `fold_2023` | `lightgbm_cpu` | `cpu` | 0.2761 | 0.0032 | 5 | 112684 | 35288 |
| `fwd_open_to_close_ret_10s_adj` | `fold_2023` | `hist_gradient_boosting_cpu` | `cpu` | 0.7429 | 0.0108 | 150 | 112684 | 35288 |
| `fwd_open_to_close_ret_10s_adj` | `fold_2023` | `xgboost_gpu` | `cuda` | 0.2885 | 0.0114 | 5 | 112684 | 35288 |
| `fwd_open_to_close_ret_10s_adj` | `fold_2024` | `lightgbm_cpu` | `cpu` | 1.8404 | 0.1508 | 287 | 146675 | 48456 |
| `fwd_open_to_close_ret_10s_adj` | `fold_2024` | `hist_gradient_boosting_cpu` | `cpu` | 0.5806 | 0.0141 | 150 | 146675 | 48456 |
| `fwd_open_to_close_ret_10s_adj` | `fold_2024` | `xgboost_gpu` | `cuda` | 0.7962 | 0.0149 | 131 | 146675 | 48456 |
| `fwd_open_to_close_ret_10s_adj` | `fold_2025` | `lightgbm_cpu` | `cpu` | 0.4557 | 0.0040 | 1 | 194386 | 64164 |
| `fwd_open_to_close_ret_10s_adj` | `fold_2025` | `hist_gradient_boosting_cpu` | `cpu` | 0.8707 | 0.0485 | 150 | 194386 | 64164 |
| `fwd_open_to_close_ret_10s_adj` | `fold_2025` | `xgboost_gpu` | `cuda` | 0.4813 | 0.0236 | 1 | 194386 | 64164 |
| `fwd_open_to_close_ret_20s_adj` | `fold_2023` | `lightgbm_cpu` | `cpu` | 0.2538 | 0.0022 | 1 | 112561 | 35253 |
| `fwd_open_to_close_ret_20s_adj` | `fold_2023` | `hist_gradient_boosting_cpu` | `cpu` | 0.6584 | 0.0110 | 150 | 112561 | 35253 |
| `fwd_open_to_close_ret_20s_adj` | `fold_2023` | `xgboost_gpu` | `cuda` | 0.2750 | 0.0082 | 2 | 112561 | 35253 |
| `fwd_open_to_close_ret_20s_adj` | `fold_2024` | `lightgbm_cpu` | `cpu` | 0.7369 | 0.0307 | 68 | 146526 | 48387 |
| `fwd_open_to_close_ret_20s_adj` | `fold_2024` | `hist_gradient_boosting_cpu` | `cpu` | 0.7785 | 0.0341 | 150 | 146526 | 48387 |
| `fwd_open_to_close_ret_20s_adj` | `fold_2024` | `xgboost_gpu` | `cuda` | 0.5744 | 0.0132 | 51 | 146526 | 48387 |
| `fwd_open_to_close_ret_20s_adj` | `fold_2025` | `lightgbm_cpu` | `cpu` | 0.4614 | 0.0037 | 1 | 194183 | 64120 |
| `fwd_open_to_close_ret_20s_adj` | `fold_2025` | `hist_gradient_boosting_cpu` | `cpu` | 0.8091 | 0.0180 | 150 | 194183 | 64120 |
| `fwd_open_to_close_ret_20s_adj` | `fold_2025` | `xgboost_gpu` | `cuda` | 0.4903 | 0.0249 | 1 | 194183 | 64120 |
| `up_5s` | `fold_2023` | `lightgbm_cpu` | `cpu` | 0.2512 | 0.0025 | 1 | 112787 | 35317 |
| `up_5s` | `fold_2023` | `hist_gradient_boosting_cpu` | `cpu` | 0.9825 | 0.0117 | 150 | 112787 | 35317 |
| `up_5s` | `fold_2023` | `xgboost_gpu` | `cuda` | 0.2729 | 0.0085 | 2 | 112787 | 35317 |
| `up_5s` | `fold_2024` | `lightgbm_cpu` | `cpu` | 1.1285 | 0.0491 | 78 | 146793 | 48505 |
| `up_5s` | `fold_2024` | `hist_gradient_boosting_cpu` | `cpu` | 1.1322 | 0.0149 | 150 | 146793 | 48505 |
| `up_5s` | `fold_2024` | `xgboost_gpu` | `cuda` | 0.8214 | 0.0164 | 161 | 146793 | 48505 |
| `up_5s` | `fold_2025` | `lightgbm_cpu` | `cpu` | 0.4559 | 0.0039 | 1 | 194556 | 64191 |
| `up_5s` | `fold_2025` | `hist_gradient_boosting_cpu` | `cpu` | 0.7917 | 0.0187 | 150 | 194556 | 64191 |
| `up_5s` | `fold_2025` | `xgboost_gpu` | `cuda` | 0.5038 | 0.0264 | 2 | 194556 | 64191 |
| `up_10s` | `fold_2023` | `lightgbm_cpu` | `cpu` | 0.2706 | 0.0029 | 3 | 112684 | 35288 |
| `up_10s` | `fold_2023` | `hist_gradient_boosting_cpu` | `cpu` | 0.5412 | 0.1118 | 150 | 112684 | 35288 |
| `up_10s` | `fold_2023` | `xgboost_gpu` | `cuda` | 0.2961 | 0.0138 | 2 | 112684 | 35288 |
| `up_10s` | `fold_2024` | `lightgbm_cpu` | `cpu` | 1.5927 | 0.0794 | 127 | 146675 | 48456 |
| `up_10s` | `fold_2024` | `hist_gradient_boosting_cpu` | `cpu` | 0.5526 | 0.0162 | 150 | 146675 | 48456 |
| `up_10s` | `fold_2024` | `xgboost_gpu` | `cuda` | 0.6967 | 0.0168 | 147 | 146675 | 48456 |
| `up_10s` | `fold_2025` | `lightgbm_cpu` | `cpu` | 0.4575 | 0.0041 | 1 | 194386 | 64164 |
| `up_10s` | `fold_2025` | `hist_gradient_boosting_cpu` | `cpu` | 0.8671 | 0.0191 | 150 | 194386 | 64164 |
| `up_10s` | `fold_2025` | `xgboost_gpu` | `cuda` | 0.4881 | 0.0252 | 1 | 194386 | 64164 |
| `up_20s` | `fold_2023` | `lightgbm_cpu` | `cpu` | 0.2539 | 0.0025 | 1 | 112561 | 35253 |
| `up_20s` | `fold_2023` | `hist_gradient_boosting_cpu` | `cpu` | 1.3609 | 0.0114 | 150 | 112561 | 35253 |
| `up_20s` | `fold_2023` | `xgboost_gpu` | `cuda` | 0.3009 | 0.0134 | 2 | 112561 | 35253 |
| `up_20s` | `fold_2024` | `lightgbm_cpu` | `cpu` | 0.5782 | 0.0092 | 23 | 146526 | 48387 |
| `up_20s` | `fold_2024` | `hist_gradient_boosting_cpu` | `cpu` | 0.6385 | 0.0196 | 150 | 146526 | 48387 |
| `up_20s` | `fold_2024` | `xgboost_gpu` | `cuda` | 0.4770 | 0.0210 | 35 | 146526 | 48387 |
| `up_20s` | `fold_2025` | `lightgbm_cpu` | `cpu` | 0.4658 | 0.0040 | 1 | 194183 | 64120 |
| `up_20s` | `fold_2025` | `hist_gradient_boosting_cpu` | `cpu` | 0.7325 | 0.0210 | 150 | 194183 | 64120 |
| `up_20s` | `fold_2025` | `xgboost_gpu` | `cuda` | 0.4957 | 0.0246 | 1 | 194183 | 64120 |

## Early stopping and prediction diagnostics

| Task/fold/model | Best iter | Metric | Best inner | First | Last evaluated | Mean | Std | Min | Max | Unique | Near constant |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `fwd_open_to_close_ret_5s_adj:fold_2023:lightgbm_cpu` | 4 | `l2` | 0.003407305009992359 | 0.0034248643532925277 | 34 | 0.00065874736 | 0.001821589 | -0.0067958453 | 0.023366029 | 32 | False |
| `fwd_open_to_close_ret_5s_adj:fold_2023:hist_gradient_boosting_cpu` | 150 | `None` | None | None | 150 | 0.0075310214 | 0.020948452 | -0.12886565 | 0.22207306 | 34546 | False |
| `fwd_open_to_close_ret_5s_adj:fold_2023:xgboost_gpu` | 3 | `rmse` | 0.05846263760378854 | 0.05850782686071911 | 33 | 0.00015263813 | 0.0010615609 | -0.0063766474 | 0.015857551 | 198 | False |
| `fwd_open_to_close_ret_5s_adj:fold_2024:lightgbm_cpu` | 129 | `l2` | 0.005460392117810566 | 0.005573653518849677 | 159 | -0.0074260511 | 0.014258722 | -0.051537558 | 0.09651202 | 25490 | False |
| `fwd_open_to_close_ret_5s_adj:fold_2024:hist_gradient_boosting_cpu` | 150 | `None` | None | None | 150 | -0.0072324154 | 0.018625581 | -0.11791736 | 0.12498383 | 48129 | False |
| `fwd_open_to_close_ret_5s_adj:fold_2024:xgboost_gpu` | 78 | `rmse` | 0.07377001242830102 | 0.07465839806478901 | 108 | -0.0078924515 | 0.014949039 | -0.053866591 | 0.1149722 | 21970 | False |
| `fwd_open_to_close_ret_5s_adj:fold_2025:lightgbm_cpu` | 1 | `l2` | 0.00876156385355757 | 0.00876156385355757 | 31 | 0.0039310565 | 0.00090954036 | 0.0025667357 | 0.010660282 | 10 | False |
| `fwd_open_to_close_ret_5s_adj:fold_2025:hist_gradient_boosting_cpu` | 150 | `None` | None | None | 150 | 0.026078752 | 0.025117028 | -0.075402518 | 0.18950133 | 63189 | False |
| `fwd_open_to_close_ret_5s_adj:fold_2025:xgboost_gpu` | 2 | `rmse` | 0.09358458293014972 | 0.09359510845567749 | 32 | 0.0032102804 | 0.0008398272 | -3.9420556e-05 | 0.011634001 | 169 | False |
| `fwd_open_to_close_ret_10s_adj:fold_2023:lightgbm_cpu` | 5 | `l2` | 0.006421191300345385 | 0.006479393010081752 | 35 | 0.0024538772 | 0.0033992262 | -0.0076589876 | 0.033502224 | 75 | False |
| `fwd_open_to_close_ret_10s_adj:fold_2023:hist_gradient_boosting_cpu` | 150 | `None` | None | None | 150 | 0.0078376731 | 0.028119602 | -0.13244009 | 0.2313996 | 34353 | False |
| `fwd_open_to_close_ret_10s_adj:fold_2023:xgboost_gpu` | 5 | `rmse` | 0.08031026148699627 | 0.08056196382760017 | 35 | 0.0018763417 | 0.0025839195 | -0.008600031 | 0.033878662 | 389 | False |
| `fwd_open_to_close_ret_10s_adj:fold_2024:lightgbm_cpu` | 287 | `l2` | 0.012071223411934107 | 0.012893840247182388 | 317 | -0.013797823 | 0.025642886 | -0.14023743 | 0.20216948 | 46803 | False |
| `fwd_open_to_close_ret_10s_adj:fold_2024:hist_gradient_boosting_cpu` | 150 | `None` | None | None | 150 | -0.015596978 | 0.029684591 | -0.15333585 | 0.20344501 | 47828 | False |
| `fwd_open_to_close_ret_10s_adj:fold_2024:xgboost_gpu` | 131 | `rmse` | 0.10967981520409245 | 0.11349345684105346 | 161 | -0.014174511 | 0.025272128 | -0.14207816 | 0.20140755 | 44752 | False |
| `fwd_open_to_close_ret_10s_adj:fold_2025:lightgbm_cpu` | 1 | `l2` | 0.02152311012539801 | 0.02152311012539801 | 31 | 0.011485941 | 0.0019160686 | 0.0073886617 | 0.01312161 | 9 | False |
| `fwd_open_to_close_ret_10s_adj:fold_2025:hist_gradient_boosting_cpu` | 150 | `None` | None | None | 150 | 0.097186751 | 0.054490821 | -0.12780383 | 0.28037819 | 62329 | False |
| `fwd_open_to_close_ret_10s_adj:fold_2025:xgboost_gpu` | 1 | `rmse` | 0.14671417573035014 | 0.14671417573035014 | 31 | 0.011482442 | 0.0021093137 | 0.0067627891 | 0.013862787 | 20 | False |
| `fwd_open_to_close_ret_20s_adj:fold_2023:lightgbm_cpu` | 1 | `l2` | 0.012082824244505255 | 0.012082824244505255 | 31 | 0.0052594157 | 0.0007887204 | 0.0022087885 | 0.016810961 | 15 | False |
| `fwd_open_to_close_ret_20s_adj:fold_2023:hist_gradient_boosting_cpu` | 150 | `None` | None | None | 150 | -0.026484033 | 0.062528629 | -0.24091528 | 0.36926843 | 35168 | False |
| `fwd_open_to_close_ret_20s_adj:fold_2023:xgboost_gpu` | 2 | `rmse` | 0.10991180987058023 | 0.10993169092668319 | 32 | 0.0051062963 | 0.0010361965 | -0.00017622113 | 0.021197807 | 155 | False |
| `fwd_open_to_close_ret_20s_adj:fold_2024:lightgbm_cpu` | 68 | `l2` | 0.03292659211634319 | 0.03341356428255712 | 98 | -0.025747754 | 0.038517907 | -0.092233308 | 0.084795634 | 15857 | False |
| `fwd_open_to_close_ret_20s_adj:fold_2024:hist_gradient_boosting_cpu` | 150 | `None` | None | None | 150 | -0.038541513 | 0.051157193 | -0.17794227 | 0.29126367 | 48187 | False |
| `fwd_open_to_close_ret_20s_adj:fold_2024:xgboost_gpu` | 51 | `rmse` | 0.18198036685021174 | 0.18280041997561997 | 81 | -0.023421145 | 0.037254489 | -0.13420777 | 0.1704035 | 23297 | False |
| `fwd_open_to_close_ret_20s_adj:fold_2025:lightgbm_cpu` | 1 | `l2` | 0.07686591017895861 | 0.07686591017895861 | 31 | 0.023298854 | 0.0020864607 | 0.01777217 | 0.046287226 | 13 | False |
| `fwd_open_to_close_ret_20s_adj:fold_2025:hist_gradient_boosting_cpu` | 150 | `None` | None | None | 150 | 0.11716583 | 0.072975978 | -0.30823184 | 0.8803667 | 62243 | False |
| `fwd_open_to_close_ret_20s_adj:fold_2025:xgboost_gpu` | 1 | `rmse` | 0.2772349934930509 | 0.2772349934930509 | 31 | 0.023219737 | 0.002537989 | 0.015790213 | 0.030657981 | 21 | False |
| `up_5s:fold_2023:lightgbm_cpu` | 1 | `binary_logloss` | 0.6803721333804353 | 0.6803721333804353 | 31 | 0.45080338 | 0.0026534717 | 0.44385444 | 0.46306251 | 13 | False |
| `up_5s:fold_2023:hist_gradient_boosting_cpu` | 150 | `None` | None | None | 150 | 0.47201909 | 0.11594767 | 0.14018227 | 0.91337361 | 35307 | False |
| `up_5s:fold_2023:xgboost_gpu` | 2 | `logloss` | 0.6805558657764469 | 0.6806272899417788 | 32 | 0.44951339 | 0.0037184125 | 0.43970752 | 0.47441527 | 250 | False |
| `up_5s:fold_2024:lightgbm_cpu` | 78 | `binary_logloss` | 0.6932582551718227 | 0.7103084738541119 | 108 | 0.39008145 | 0.095688095 | 0.23203569 | 0.76408311 | 42418 | False |
| `up_5s:fold_2024:hist_gradient_boosting_cpu` | 150 | `None` | None | None | 150 | 0.37678798 | 0.11615264 | 0.14202595 | 0.85214375 | 48479 | False |
| `up_5s:fold_2024:xgboost_gpu` | 161 | `logloss` | 0.6935215165022632 | 0.7106227700800871 | 191 | 0.38221236 | 0.10813264 | 0.14834028 | 0.83666128 | 47698 | False |
| `up_5s:fold_2025:lightgbm_cpu` | 1 | `binary_logloss` | 0.6952078448996858 | 0.6952078448996858 | 31 | 0.46504942 | 0.0050820634 | 0.45901572 | 0.47484316 | 9 | False |
| `up_5s:fold_2025:hist_gradient_boosting_cpu` | 150 | `None` | None | None | 150 | 0.54838359 | 0.12020708 | 0.19155792 | 0.93451919 | 64114 | False |
| `up_5s:fold_2025:xgboost_gpu` | 2 | `logloss` | 0.6950559128427133 | 0.695060795007823 | 32 | 0.46459057 | 0.0053650695 | 0.45345929 | 0.48747611 | 294 | False |
| `up_10s:fold_2023:lightgbm_cpu` | 3 | `binary_logloss` | 0.6797848777919083 | 0.6799764656346284 | 33 | 0.45757049 | 0.0068912708 | 0.43738013 | 0.48847113 | 56 | False |
| `up_10s:fold_2023:hist_gradient_boosting_cpu` | 150 | `None` | None | None | 150 | 0.48131479 | 0.12106951 | 0.095721313 | 0.87521077 | 35271 | False |
| `up_10s:fold_2023:xgboost_gpu` | 2 | `logloss` | 0.6798767299158435 | 0.6799444292107331 | 32 | 0.4560422 | 0.0032466654 | 0.44454497 | 0.47364992 | 177 | False |
| `up_10s:fold_2024:lightgbm_cpu` | 127 | `binary_logloss` | 0.67895962673099 | 0.7182388393466747 | 157 | 0.3667345 | 0.11859178 | 0.17497016 | 0.77506086 | 47630 | False |
| `up_10s:fold_2024:hist_gradient_boosting_cpu` | 150 | `None` | None | None | 150 | 0.36088332 | 0.13029822 | 0.11765604 | 0.83602568 | 48443 | False |
| `up_10s:fold_2024:xgboost_gpu` | 147 | `logloss` | 0.6802617741208541 | 0.7188131116987908 | 177 | 0.37005171 | 0.12296353 | 0.14111702 | 0.79775089 | 47622 | False |
| `up_10s:fold_2025:lightgbm_cpu` | 1 | `binary_logloss` | 0.7001457753984663 | 0.7001457753984663 | 31 | 0.48774721 | 0.0049681488 | 0.47289605 | 0.48984788 | 6 | False |
| `up_10s:fold_2025:hist_gradient_boosting_cpu` | 150 | `None` | None | None | 150 | 0.77381611 | 0.16904918 | 0.16973685 | 0.94758212 | 63872 | False |
| `up_10s:fold_2025:xgboost_gpu` | 1 | `logloss` | 0.70024282096857 | 0.70024282096857 | 31 | 0.4874491 | 0.0055245674 | 0.47338662 | 0.49097291 | 17 | False |
| `up_20s:fold_2023:lightgbm_cpu` | 1 | `binary_logloss` | 0.6810429009852209 | 0.6810429009852209 | 31 | 0.4576418 | 0.0032322636 | 0.45144516 | 0.46790984 | 11 | False |
| `up_20s:fold_2023:hist_gradient_boosting_cpu` | 150 | `None` | None | None | 150 | 0.42827054 | 0.14845584 | 0.077555561 | 0.86062285 | 35237 | False |
| `up_20s:fold_2023:xgboost_gpu` | 2 | `logloss` | 0.6809911528551623 | 0.6811403206404792 | 32 | 0.45721798 | 0.0039944066 | 0.44497594 | 0.47454044 | 151 | False |
| `up_20s:fold_2024:lightgbm_cpu` | 23 | `binary_logloss` | 0.7248035741953436 | 0.7308732867560865 | 53 | 0.40389682 | 0.07357647 | 0.33841463 | 0.6067358 | 683 | False |
| `up_20s:fold_2024:hist_gradient_boosting_cpu` | 150 | `None` | None | None | 150 | 0.3130072 | 0.15967296 | 0.082740855 | 0.85448243 | 48339 | False |
| `up_20s:fold_2024:xgboost_gpu` | 35 | `logloss` | 0.7244877998965387 | 0.7308961762172228 | 65 | 0.39428107 | 0.085159242 | 0.25421461 | 0.63770193 | 22564 | False |
| `up_20s:fold_2025:lightgbm_cpu` | 1 | `binary_logloss` | 0.7063362500707832 | 0.7063362500707832 | 31 | 0.49709277 | 0.0046834301 | 0.48400041 | 0.49923859 | 6 | False |
| `up_20s:fold_2025:hist_gradient_boosting_cpu` | 150 | `None` | None | None | 150 | 0.74094748 | 0.16794592 | 0.16072718 | 0.92289798 | 63786 | False |
| `up_20s:fold_2025:xgboost_gpu` | 1 | `logloss` | 0.7066920380827934 | 0.7066920380827934 | 31 | 0.49818282 | 0.0052077291 | 0.4833557 | 0.50069922 | 19 | False |
