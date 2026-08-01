# C6 Robust Evaluation Report

Stored fixed C5 validation predictions are filtered without refitting. The final holdout remains locked. These are predictive/ranking diagnostics, not portfolio returns or profitability evidence.

## Overall metrics

| Universe | Target | Model | N | MAE | Median AE | RMSE | Huber | Pearson | Spearman / ROC AUC | Daily IC |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `pit_liquid_all_instruments_v1` | `fwd_open_to_close_ret_10s_adj` | `ridge_fixed_alpha_1` | 150184 | 0.07543505598521824 | 0.05009657508774437 | 0.14275010768402602 | 0.0042020704769179 | -0.15266140302251566 | -0.08458224036980999 | -0.05812391067743439 |
| `pit_liquid_all_instruments_v1` | `fwd_open_to_close_ret_10s_adj` | `training_mean_baseline` | 150184 | 0.07323310535798826 | 0.04900986364644819 | 0.12014213640598426 | 0.004012124093694915 | -0.020771480240022292 | -0.041004715267526 |  |
| `pit_liquid_all_instruments_v1` | `fwd_open_to_close_ret_10s_adj` | `zero_return_baseline` | 150184 | 0.07289450210184274 | 0.047981136612234576 | 0.12067845174513063 | 0.004011707683708074 |  |  |  |
| `pit_liquid_all_instruments_v1` | `fwd_open_to_close_ret_20s_adj` | `ridge_fixed_alpha_1` | 150017 | 0.11048163963993164 | 0.07332362983824858 | 0.2979556485200924 | 0.007248009691550294 | -0.03942457033919159 | -0.0798540631362712 | -0.05784990731325381 |
| `pit_liquid_all_instruments_v1` | `fwd_open_to_close_ret_20s_adj` | `training_mean_baseline` | 150017 | 0.10617200283835357 | 0.07083721673172183 | 0.20841463841950653 | 0.006854982474991327 | -0.023779870124073305 | -0.0435532701865304 |  |
| `pit_liquid_all_instruments_v1` | `fwd_open_to_close_ret_20s_adj` | `zero_return_baseline` | 150017 | 0.10588776357919635 | 0.06833578792341688 | 0.2102361899523141 | 0.006882611725928463 |  |  |  |
| `pit_liquid_all_instruments_v1` | `fwd_open_to_close_ret_5s_adj` | `ridge_fixed_alpha_1` | 150304 | 0.05376004746404124 | 0.035508086751589146 | 0.10341023037744498 | 0.0024982005261339263 | 0.008160175481385036 | -0.06471167889238932 | -0.032225470451019894 |
| `pit_liquid_all_instruments_v1` | `fwd_open_to_close_ret_5s_adj` | `training_mean_baseline` | 150304 | 0.05287360981446523 | 0.03519837739807474 | 0.08247801703250976 | 0.0024235706082720776 | -0.02245003262374811 | -0.04362375878116027 |  |
| `pit_liquid_all_instruments_v1` | `fwd_open_to_close_ret_5s_adj` | `zero_return_baseline` | 150304 | 0.05268439716199725 | 0.03482583371164133 | 0.0825688946281948 | 0.0024207547924995324 |  |  |  |
| `pit_liquid_all_instruments_v1` | `up_10s` | `logistic_fixed_c_1` | 150184 |  |  |  |  |  | 0.483958226958554 |  |
| `pit_liquid_all_instruments_v1` | `up_10s` | `majority_class_baseline` | 150184 |  |  |  |  |  | 0.5 |  |
| `pit_liquid_all_instruments_v1` | `up_10s` | `training_prevalence_baseline` | 150184 |  |  |  |  |  | 0.478357080547294 |  |
| `pit_liquid_all_instruments_v1` | `up_20s` | `logistic_fixed_c_1` | 150017 |  |  |  |  |  | 0.48894711444265426 |  |
| `pit_liquid_all_instruments_v1` | `up_20s` | `majority_class_baseline` | 150017 |  |  |  |  |  | 0.5 |  |
| `pit_liquid_all_instruments_v1` | `up_20s` | `training_prevalence_baseline` | 150017 |  |  |  |  |  | 0.48316145895709767 |  |
| `pit_liquid_all_instruments_v1` | `up_5s` | `logistic_fixed_c_1` | 150304 |  |  |  |  |  | 0.49694980228670493 |  |
| `pit_liquid_all_instruments_v1` | `up_5s` | `majority_class_baseline` | 150304 |  |  |  |  |  | 0.5 |  |
| `pit_liquid_all_instruments_v1` | `up_5s` | `training_prevalence_baseline` | 150304 |  |  |  |  |  | 0.4757010543866551 |  |
| `pit_liquid_equity_like_v1` | `fwd_open_to_close_ret_10s_adj` | `ridge_fixed_alpha_1` | 148668 | 0.0756467936614113 | 0.05041239249631414 | 0.14234631746064605 | 0.00421396222954554 | -0.15889349564426458 | -0.08386077442899144 | -0.05879439388827742 |
| `pit_liquid_equity_like_v1` | `fwd_open_to_close_ret_10s_adj` | `training_mean_baseline` | 148668 | 0.07364125957228065 | 0.04936684423926194 | 0.12063819687051086 | 0.004040423417297366 | -0.0200870909762094 | -0.041116022577068596 |  |
| `pit_liquid_equity_like_v1` | `fwd_open_to_close_ret_10s_adj` | `zero_return_baseline` | 148668 | 0.07328936879506814 | 0.048278731075173886 | 0.12117686632481461 | 0.0040398398977270706 |  |  |  |
| `pit_liquid_equity_like_v1` | `fwd_open_to_close_ret_20s_adj` | `ridge_fixed_alpha_1` | 148520 | 0.10961707163929273 | 0.07369468465208334 | 0.21302131642710445 | 0.007155538640195682 | -0.1637864503278028 | -0.07930383087135015 | -0.05867543345383509 |
| `pit_liquid_equity_like_v1` | `fwd_open_to_close_ret_20s_adj` | `training_mean_baseline` | 148520 | 0.1062385132166511 | 0.0712566361717979 | 0.19832588361696873 | 0.006850896787368668 | -0.020607876977121572 | -0.04354241712945202 |  |
| `pit_liquid_equity_like_v1` | `fwd_open_to_close_ret_20s_adj` | `zero_return_baseline` | 148520 | 0.1059236024114147 | 0.06864910111003858 | 0.20024217863643123 | 0.00687788591763586 |  |  |  |
| `pit_liquid_equity_like_v1` | `fwd_open_to_close_ret_5s_adj` | `ridge_fixed_alpha_1` | 148773 | 0.05376844264953218 | 0.035720966582089335 | 0.08626348435841327 | 0.002489016743476092 | 0.020092831432094248 | -0.06364544857633127 | -0.03224348877547733 |
| `pit_liquid_equity_like_v1` | `fwd_open_to_close_ret_5s_adj` | `training_mean_baseline` | 148773 | 0.05318234886065579 | 0.035460802437735986 | 0.08281194640195276 | 0.002441580033362874 | -0.02191974177509702 | -0.04385372612186046 |  |
| `pit_liquid_equity_like_v1` | `fwd_open_to_close_ret_5s_adj` | `zero_return_baseline` | 148773 | 0.052988796164633686 | 0.03508771929824561 | 0.08290349532409672 | 0.0024387289213551847 |  |  |  |
| `pit_liquid_equity_like_v1` | `up_10s` | `logistic_fixed_c_1` | 148668 |  |  |  |  |  | 0.48464243825418746 |  |
| `pit_liquid_equity_like_v1` | `up_10s` | `majority_class_baseline` | 148668 |  |  |  |  |  | 0.5 |  |
| `pit_liquid_equity_like_v1` | `up_10s` | `training_prevalence_baseline` | 148668 |  |  |  |  |  | 0.47782220754510407 |  |
| `pit_liquid_equity_like_v1` | `up_20s` | `logistic_fixed_c_1` | 148520 |  |  |  |  |  | 0.48876767541937893 |  |
| `pit_liquid_equity_like_v1` | `up_20s` | `majority_class_baseline` | 148520 |  |  |  |  |  | 0.5 |  |
| `pit_liquid_equity_like_v1` | `up_20s` | `training_prevalence_baseline` | 148520 |  |  |  |  |  | 0.4826223801834377 |  |
| `pit_liquid_equity_like_v1` | `up_5s` | `logistic_fixed_c_1` | 148773 |  |  |  |  |  | 0.497098027300651 |  |
| `pit_liquid_equity_like_v1` | `up_5s` | `majority_class_baseline` | 148773 |  |  |  |  |  | 0.5 |  |
| `pit_liquid_equity_like_v1` | `up_5s` | `training_prevalence_baseline` | 148773 |  |  |  |  |  | 0.4753199069942273 |  |
| `pit_liquid_ordinary_equity_v1` | `fwd_open_to_close_ret_10s_adj` | `ridge_fixed_alpha_1` | 147908 | 0.07587244105902746 | 0.050656118694057464 | 0.14266820188787216 | 0.004229971496918114 | -0.15890913454102898 | -0.08328359598201329 | -0.05768749423707349 |
| `pit_liquid_ordinary_equity_v1` | `fwd_open_to_close_ret_10s_adj` | `training_mean_baseline` | 147908 | 0.07387290805668255 | 0.049602279895656944 | 0.12090449115648699 | 0.004056317734721941 | -0.020253726937038394 | -0.04152917984909768 |  |
| `pit_liquid_ordinary_equity_v1` | `fwd_open_to_close_ret_10s_adj` | `zero_return_baseline` | 147908 | 0.07351675941246891 | 0.04850459365291082 | 0.12144211939168398 | 0.004055472049480781 |  |  |  |
| `pit_liquid_ordinary_equity_v1` | `fwd_open_to_close_ret_20s_adj` | `ridge_fixed_alpha_1` | 147760 | 0.1099430310698618 | 0.0740009758683504 | 0.21351647020033035 | 0.007182561840465375 | -0.16380979164514736 | -0.07863074772789536 | -0.05808556025615658 |
| `pit_liquid_ordinary_equity_v1` | `fwd_open_to_close_ret_20s_adj` | `training_mean_baseline` | 147760 | 0.10658290258930132 | 0.07158152333932871 | 0.19879487375834273 | 0.0068787331211117705 | -0.02083391930865365 | -0.0441826463976855 |  |
| `pit_liquid_ordinary_equity_v1` | `fwd_open_to_close_ret_20s_adj` | `zero_return_baseline` | 147760 | 0.10625193108803589 | 0.06896551724137923 | 0.20070798254256506 | 0.006904500824744742 |  |  |  |
| `pit_liquid_ordinary_equity_v1` | `fwd_open_to_close_ret_5s_adj` | `ridge_fixed_alpha_1` | 148013 | 0.05393447671736646 | 0.0358771531943106 | 0.08645029957560878 | 0.002498929465658108 | 0.020153271504737662 | -0.06310115538169947 | -0.03122364987245622 |
| `pit_liquid_ordinary_equity_v1` | `fwd_open_to_close_ret_5s_adj` | `training_mean_baseline` | 148013 | 0.05335415426601525 | 0.035664600566917115 | 0.08299243679237787 | 0.002451548837970313 | -0.02206931617748692 | -0.04418743948876514 |  |
| `pit_liquid_ordinary_equity_v1` | `fwd_open_to_close_ret_5s_adj` | `zero_return_baseline` | 148013 | 0.053159009657527845 | 0.0352926829268293 | 0.08308359116033456 | 0.0024486337921298604 |  |  |  |
| `pit_liquid_ordinary_equity_v1` | `up_10s` | `logistic_fixed_c_1` | 147908 |  |  |  |  |  | 0.4848291708122861 |  |
| `pit_liquid_ordinary_equity_v1` | `up_10s` | `majority_class_baseline` | 147908 |  |  |  |  |  | 0.5 |  |
| `pit_liquid_ordinary_equity_v1` | `up_10s` | `training_prevalence_baseline` | 147908 |  |  |  |  |  | 0.47748013109491194 |  |
| `pit_liquid_ordinary_equity_v1` | `up_20s` | `logistic_fixed_c_1` | 147760 |  |  |  |  |  | 0.48900518957674355 |  |
| `pit_liquid_ordinary_equity_v1` | `up_20s` | `majority_class_baseline` | 147760 |  |  |  |  |  | 0.5 |  |
| `pit_liquid_ordinary_equity_v1` | `up_20s` | `training_prevalence_baseline` | 147760 |  |  |  |  |  | 0.4821700735349747 |  |
| `pit_liquid_ordinary_equity_v1` | `up_5s` | `logistic_fixed_c_1` | 148013 |  |  |  |  |  | 0.4972791828747942 |  |
| `pit_liquid_ordinary_equity_v1` | `up_5s` | `majority_class_baseline` | 148013 |  |  |  |  |  | 0.5 |  |
| `pit_liquid_ordinary_equity_v1` | `up_5s` | `training_prevalence_baseline` | 148013 |  |  |  |  |  | 0.4751017735329407 |  |

Stratified fold, year, liquidity-bucket, stale-bucket, and instrument-family rows are preserved in `c6_robust_metrics.parquet`. Canonical untrimmed metrics remain visible beside robust diagnostics.

## Concentration change

| Universe | Horizon | Top-1 symbol share | Top-10 symbol share | Largest contributor |
|---|---|---:|---:|---|
| `pit_liquid_all_instruments_v1` | `fwd_open_to_close_ret_10s_adj` | 0.328223 | 0.413564 | `PHDL` |
| `pit_liquid_all_instruments_v1` | `fwd_open_to_close_ret_20s_adj` | 0.429662 | 0.706234 | `P01GIS150825` |
| `pit_liquid_all_instruments_v1` | `fwd_open_to_close_ret_5s_adj` | 0.294827 | 0.425695 | `P01GIS150825` |
| `pit_liquid_equity_like_v1` | `fwd_open_to_close_ret_10s_adj` | 0.333454 | 0.415031 | `PHDL` |
| `pit_liquid_equity_like_v1` | `fwd_open_to_close_ret_20s_adj` | 0.324153 | 0.450348 | `PHDL` |
| `pit_liquid_equity_like_v1` | `fwd_open_to_close_ret_5s_adj` | 0.107819 | 0.190966 | `PHDL` |
| `pit_liquid_ordinary_equity_v1` | `fwd_open_to_close_ret_10s_adj` | 0.333656 | 0.415283 | `PHDL` |
| `pit_liquid_ordinary_equity_v1` | `fwd_open_to_close_ret_20s_adj` | 0.324311 | 0.450567 | `PHDL` |
| `pit_liquid_ordinary_equity_v1` | `fwd_open_to_close_ret_5s_adj` | 0.107904 | 0.191118 | `PHDL` |

The ordinary-equity filter sharply reduces 5- and 20-session concentration by removing structurally different fixed-income observations, including `P01GIS150825`. Ten-session loss remains dominated by ordinary-equity outliers such as `PHDL`.

Correlations and daily IC remain weak or negative, and classification ROC AUC remains near or below 0.5. The negative C5 linear conclusion therefore does not change.

## C7 universe decision

Recommend `pit_liquid_ordinary_equity_v1` for C7 on structural instrument-family grounds and broad coverage—not because filtered RMSE is lower. The current-master historical backcast limitation remains explicit.
