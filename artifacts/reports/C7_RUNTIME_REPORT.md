# C7 Runtime Report

Canonical CPU mode uses one thread; XGBoost verification uses CUDA on `NVIDIA GeForce RTX 5070 Laptop GPU`.

| Task | Fold | Model | Device | Fit s | Predict s | Rounds | Train rows | Validation rows |
|---|---|---|---|---:|---:|---:|---:|---:|
| `fwd_open_to_close_ret_5s_adj` | `fold_2023` | `lightgbm_cpu` | `cpu` | 0.2628 | 0.0029 | 4 | 112787 | 35317 |
| `fwd_open_to_close_ret_5s_adj` | `fold_2023` | `hist_gradient_boosting_cpu` | `cpu` | 2.0123 | 0.0111 | 150 | 112787 | 35317 |
| `fwd_open_to_close_ret_5s_adj` | `fold_2023` | `xgboost_gpu` | `cuda` | 0.2862 | 0.0131 | 3 | 112787 | 35317 |
| `fwd_open_to_close_ret_5s_adj` | `fold_2024` | `lightgbm_cpu` | `cpu` | 1.0389 | 0.0554 | 129 | 146793 | 48505 |
| `fwd_open_to_close_ret_5s_adj` | `fold_2024` | `hist_gradient_boosting_cpu` | `cpu` | 1.3355 | 0.0724 | 150 | 146793 | 48505 |
| `fwd_open_to_close_ret_5s_adj` | `fold_2024` | `xgboost_gpu` | `cuda` | 0.5170 | 0.0131 | 78 | 146793 | 48505 |
| `fwd_open_to_close_ret_5s_adj` | `fold_2025` | `lightgbm_cpu` | `cpu` | 0.4565 | 0.0036 | 1 | 194556 | 64191 |
| `fwd_open_to_close_ret_5s_adj` | `fold_2025` | `hist_gradient_boosting_cpu` | `cpu` | 3.2065 | 0.0211 | 150 | 194556 | 64191 |
| `fwd_open_to_close_ret_5s_adj` | `fold_2025` | `xgboost_gpu` | `cuda` | 0.4830 | 0.0246 | 2 | 194556 | 64191 |
| `fwd_open_to_close_ret_10s_adj` | `fold_2023` | `lightgbm_cpu` | `cpu` | 0.2665 | 0.0031 | 5 | 112684 | 35288 |
| `fwd_open_to_close_ret_10s_adj` | `fold_2023` | `hist_gradient_boosting_cpu` | `cpu` | 1.3479 | 0.0106 | 150 | 112684 | 35288 |
| `fwd_open_to_close_ret_10s_adj` | `fold_2023` | `xgboost_gpu` | `cuda` | 0.3015 | 0.0113 | 5 | 112684 | 35288 |
| `fwd_open_to_close_ret_10s_adj` | `fold_2024` | `lightgbm_cpu` | `cpu` | 1.8237 | 0.1500 | 287 | 146675 | 48456 |
| `fwd_open_to_close_ret_10s_adj` | `fold_2024` | `hist_gradient_boosting_cpu` | `cpu` | 0.5000 | 0.0141 | 150 | 146675 | 48456 |
| `fwd_open_to_close_ret_10s_adj` | `fold_2024` | `xgboost_gpu` | `cuda` | 0.6484 | 0.0142 | 131 | 146675 | 48456 |
| `fwd_open_to_close_ret_10s_adj` | `fold_2025` | `lightgbm_cpu` | `cpu` | 0.4526 | 0.0038 | 1 | 194386 | 64164 |
| `fwd_open_to_close_ret_10s_adj` | `fold_2025` | `hist_gradient_boosting_cpu` | `cpu` | 0.5648 | 0.0172 | 150 | 194386 | 64164 |
| `fwd_open_to_close_ret_10s_adj` | `fold_2025` | `xgboost_gpu` | `cuda` | 0.4898 | 0.0240 | 1 | 194386 | 64164 |
| `fwd_open_to_close_ret_20s_adj` | `fold_2023` | `lightgbm_cpu` | `cpu` | 0.2507 | 0.0022 | 1 | 112561 | 35253 |
| `fwd_open_to_close_ret_20s_adj` | `fold_2023` | `hist_gradient_boosting_cpu` | `cpu` | 0.6082 | 0.0185 | 150 | 112561 | 35253 |
| `fwd_open_to_close_ret_20s_adj` | `fold_2023` | `xgboost_gpu` | `cuda` | 0.2909 | 0.0136 | 2 | 112561 | 35253 |
| `fwd_open_to_close_ret_20s_adj` | `fold_2024` | `lightgbm_cpu` | `cpu` | 0.7336 | 0.0308 | 68 | 146526 | 48387 |
| `fwd_open_to_close_ret_20s_adj` | `fold_2024` | `hist_gradient_boosting_cpu` | `cpu` | 2.3092 | 0.0137 | 150 | 146526 | 48387 |
| `fwd_open_to_close_ret_20s_adj` | `fold_2024` | `xgboost_gpu` | `cuda` | 0.5457 | 0.0164 | 51 | 146526 | 48387 |
| `fwd_open_to_close_ret_20s_adj` | `fold_2025` | `lightgbm_cpu` | `cpu` | 0.4565 | 0.0035 | 1 | 194183 | 64120 |
| `fwd_open_to_close_ret_20s_adj` | `fold_2025` | `hist_gradient_boosting_cpu` | `cpu` | 0.5209 | 0.0269 | 150 | 194183 | 64120 |
| `fwd_open_to_close_ret_20s_adj` | `fold_2025` | `xgboost_gpu` | `cuda` | 0.4737 | 0.0231 | 1 | 194183 | 64120 |
| `up_5s` | `fold_2023` | `lightgbm_cpu` | `cpu` | 0.2528 | 0.0025 | 1 | 112787 | 35317 |
| `up_5s` | `fold_2023` | `hist_gradient_boosting_cpu` | `cpu` | 0.6175 | 0.0122 | 150 | 112787 | 35317 |
| `up_5s` | `fold_2023` | `xgboost_gpu` | `cuda` | 0.2884 | 0.0161 | 2 | 112787 | 35317 |
| `up_5s` | `fold_2024` | `lightgbm_cpu` | `cpu` | 1.1184 | 0.0485 | 78 | 146793 | 48505 |
| `up_5s` | `fold_2024` | `hist_gradient_boosting_cpu` | `cpu` | 0.5068 | 0.0567 | 150 | 146793 | 48505 |
| `up_5s` | `fold_2024` | `xgboost_gpu` | `cuda` | 0.9138 | 0.0164 | 161 | 146793 | 48505 |
| `up_5s` | `fold_2025` | `lightgbm_cpu` | `cpu` | 0.4686 | 0.0043 | 1 | 194556 | 64191 |
| `up_5s` | `fold_2025` | `hist_gradient_boosting_cpu` | `cpu` | 0.5781 | 0.0187 | 150 | 194556 | 64191 |
| `up_5s` | `fold_2025` | `xgboost_gpu` | `cuda` | 0.4826 | 0.0242 | 2 | 194556 | 64191 |
| `up_10s` | `fold_2023` | `lightgbm_cpu` | `cpu` | 0.2684 | 0.0029 | 3 | 112684 | 35288 |
| `up_10s` | `fold_2023` | `hist_gradient_boosting_cpu` | `cpu` | 1.3424 | 0.0117 | 150 | 112684 | 35288 |
| `up_10s` | `fold_2023` | `xgboost_gpu` | `cuda` | 0.2990 | 0.0175 | 2 | 112684 | 35288 |
| `up_10s` | `fold_2024` | `lightgbm_cpu` | `cpu` | 1.5709 | 0.0798 | 127 | 146675 | 48456 |
| `up_10s` | `fold_2024` | `hist_gradient_boosting_cpu` | `cpu` | 0.8848 | 0.0320 | 150 | 146675 | 48456 |
| `up_10s` | `fold_2024` | `xgboost_gpu` | `cuda` | 0.6844 | 0.0207 | 147 | 146675 | 48456 |
| `up_10s` | `fold_2025` | `lightgbm_cpu` | `cpu` | 0.4641 | 0.0037 | 1 | 194386 | 64164 |
| `up_10s` | `fold_2025` | `hist_gradient_boosting_cpu` | `cpu` | 0.6776 | 0.0204 | 150 | 194386 | 64164 |
| `up_10s` | `fold_2025` | `xgboost_gpu` | `cuda` | 0.4577 | 0.0142 | 1 | 194386 | 64164 |
| `up_20s` | `fold_2023` | `lightgbm_cpu` | `cpu` | 0.2551 | 0.0024 | 1 | 112561 | 35253 |
| `up_20s` | `fold_2023` | `hist_gradient_boosting_cpu` | `cpu` | 0.5747 | 0.0131 | 150 | 112561 | 35253 |
| `up_20s` | `fold_2023` | `xgboost_gpu` | `cuda` | 0.2789 | 0.0077 | 2 | 112561 | 35253 |
| `up_20s` | `fold_2024` | `lightgbm_cpu` | `cpu` | 0.5787 | 0.0100 | 23 | 146526 | 48387 |
| `up_20s` | `fold_2024` | `hist_gradient_boosting_cpu` | `cpu` | 0.5334 | 0.0143 | 150 | 146526 | 48387 |
| `up_20s` | `fold_2024` | `xgboost_gpu` | `cuda` | 0.5056 | 0.0135 | 35 | 146526 | 48387 |
| `up_20s` | `fold_2025` | `lightgbm_cpu` | `cpu` | 0.4671 | 0.0039 | 1 | 194183 | 64120 |
| `up_20s` | `fold_2025` | `hist_gradient_boosting_cpu` | `cpu` | 1.0859 | 0.0178 | 150 | 194183 | 64120 |
| `up_20s` | `fold_2025` | `xgboost_gpu` | `cuda` | 0.4753 | 0.0315 | 1 | 194183 | 64120 |
