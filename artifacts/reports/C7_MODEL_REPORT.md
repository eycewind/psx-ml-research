# C7 Gradient-Boosted Tree Model Report

Final holdout accessed: **False**. Canonical universe: `pit_liquid_ordinary_equity_v1`.

These are predictive validation diagnostics, not signals, portfolios, backtests, or profitability results.

## Aggregate fold metrics

| Task/model | Means | Fold standard deviations | N |
|---|---|---|---:|
| `fwd_open_to_close_ret_10s_adj:hist_gradient_boosting_cpu` | `{"constant_prediction_date_count": 0.0, "constant_target_date_count": 0.0, "daily_ic_std": 0.11509718839783101, "directional_accuracy": 0.5227372096356024, "finite_ic_date_count": 247.33333333333334, "huber_loss": 0.0054980124242058545, "mae": 0.09238257934412465, "mean_daily_ic": 0.054630315145897536, "median_absolute_error": 0.07380496939693611, "median_daily_ic": 0.049903756424551825, "nonfinite_ic_date_count": 0.0, "pearson": 0.06742140937572726, "population_eligible_date_count": 247.33333333333334, "positive_ic_fraction": 0.67779945799458, "quantile_spread": 0.01000558332468376, "r2": -0.26366722378264046, "rmse": 0.1320468608959106, "spearman": 0.07287516681654481, "trimmed_rmse": 0.1320468608959106, "validation_date_count": 247.33333333333334}` | `{"constant_prediction_date_count": 0.0, "constant_target_date_count": 0.0, "daily_ic_std": 0.005719145314546116, "directional_accuracy": 0.012567782201765661, "finite_ic_date_count": 1.8856180831641267, "huber_loss": 0.0017343387946155272, "mae": 0.021551411780277266, "mean_daily_ic": 0.006803838240895008, "median_absolute_error": 0.028488747641677338, "median_daily_ic": 0.00501872130206591, "nonfinite_ic_date_count": 0.0, "pearson": 0.011375342572078595, "population_eligible_date_count": 1.8856180831641267, "positive_ic_fraction": 0.013799155694451577, "quantile_spread": 0.004515723827287492, "r2": 0.27735628597969203, "rmse": 0.021111245894353845, "spearman": 0.023307495538465315, "trimmed_rmse": 0.021111245894353845, "validation_date_count": 1.8856180831641267}` | 147908 |
| `fwd_open_to_close_ret_10s_adj:lightgbm_cpu` | `{"constant_prediction_date_count": 3.3333333333333335, "constant_target_date_count": 0.0, "daily_ic_std": 0.1210926807414542, "directional_accuracy": 0.5199674790882126, "finite_ic_date_count": 216.33333333333334, "huber_loss": 0.004111107477023632, "mae": 0.07461680234031721, "mean_daily_ic": 0.03407035386403546, "median_absolute_error": 0.05022555521102557, "median_daily_ic": 0.022401204991411513, "nonfinite_ic_date_count": 27.666666666666668, "pearson": 0.06129409872637497, "population_eligible_date_count": 247.33333333333334, "positive_ic_fraction": 0.5856385362762628, "quantile_spread": 0.004468424631948472, "r2": -0.03092153646654035, "rmse": 0.1199164863444969, "spearman": 0.055657012269441676, "trimmed_rmse": 0.11991648634449692, "validation_date_count": 247.33333333333334}` | `{"constant_prediction_date_count": 4.714045207910316, "constant_target_date_count": 0.0, "daily_ic_std": 0.010473107187197041, "directional_accuracy": 0.03211582373549074, "finite_ic_date_count": 24.931015935086872, "huber_loss": 0.0003899009107093253, "mae": 0.004075943382247605, "mean_daily_ic": 0.01290677355549837, "median_absolute_error": 0.001144146403778939, "median_daily_ic": 0.0055373213461649955, "nonfinite_ic_date_count": 21.044925490219462, "pearson": 0.008274740016188177, "population_eligible_date_count": 1.8856180831641267, "positive_ic_fraction": 0.02586591086989284, "quantile_spread": 0.007238156467129727, "r2": 0.029640411536262713, "rmse": 0.015424027755581896, "spearman": 0.015622372485223178, "trimmed_rmse": 0.01542402775558189, "validation_date_count": 1.8856180831641267}` | 147908 |
| `fwd_open_to_close_ret_10s_adj:ridge_fixed_alpha_1` | `{"constant_prediction_date_count": 0.0, "constant_target_date_count": 0.0, "daily_ic_std": 0.12888796269836336, "directional_accuracy": 0.4683124729914139, "finite_ic_date_count": 247.33333333333334, "huber_loss": 0.004216663873243026, "mae": 0.07585473767593655, "mean_daily_ic": -0.05750034198212817, "median_absolute_error": 0.051119269804776, "median_daily_ic": -0.06016618006262963, "nonfinite_ic_date_count": 0.0, "pearson": -0.10032440983921675, "population_eligible_date_count": 247.33333333333334, "positive_ic_fraction": 0.3172140921409214, "quantile_spread": -0.003638253292524926, "r2": -0.341758385955173, "rmse": 0.1370914815853918, "spearman": -0.09293292500816315, "trimmed_rmse": 0.1370914815853918, "validation_date_count": 247.33333333333334}` | `{"constant_prediction_date_count": 0.0, "constant_target_date_count": 0.0, "daily_ic_std": 0.002215155676202699, "directional_accuracy": 0.01953990066110419, "finite_ic_date_count": 1.8856180831641267, "huber_loss": 0.0003791490811981892, "mae": 0.00365023441389412, "mean_daily_ic": 0.03131957573738338, "median_absolute_error": 0.0018455839365716874, "median_daily_ic": 0.023963158092702712, "nonfinite_ic_date_count": 0.0, "pearson": 0.10400890527509292, "population_eligible_date_count": 1.8856180831641267, "positive_ic_fraction": 0.0816126543370187, "quantile_spread": 0.004059072083652834, "r2": 0.43359930872859215, "rmse": 0.03694440646087058, "spearman": 0.019874165899828277, "trimmed_rmse": 0.03694440646087058, "validation_date_count": 1.8856180831641267}` | 147908 |
| `fwd_open_to_close_ret_10s_adj:training_mean_baseline` | `{"constant_prediction_date_count": 60.0, "constant_target_date_count": 0.0, "directional_accuracy": 0.5044693705565291, "finite_ic_date_count": 0.0, "huber_loss": 0.004036497703692125, "mae": 0.0737380377003446, "median_absolute_error": 0.0498800023927209, "nonfinite_ic_date_count": 187.33333333333334, "population_eligible_date_count": 247.33333333333334, "quantile_spread": 8.761854723001186e-05, "r2": -0.015040838546295085, "rmse": 0.11881967430369128, "trimmed_rmse": 0.11881967430369128, "validation_date_count": 247.33333333333334}` | `{"constant_prediction_date_count": 51.61395160225576, "constant_target_date_count": 0.0, "directional_accuracy": 0.02376248244766233, "finite_ic_date_count": 0.0, "huber_loss": 0.0002834387725857901, "mae": 0.003025985502470214, "median_absolute_error": 0.0015519510140451908, "nonfinite_ic_date_count": 53.17476427362471, "population_eligible_date_count": 1.8856180831641267, "quantile_spread": 0.0033383370845585054, "r2": 0.012001744535401074, "rmse": 0.01366981884217039, "trimmed_rmse": 0.01366981884217039, "validation_date_count": 1.8856180831641267}` | 147908 |
| `fwd_open_to_close_ret_10s_adj:xgboost_gpu` | `{"constant_prediction_date_count": 0.6666666666666666, "constant_target_date_count": 0.0, "daily_ic_std": 0.1260156678939239, "directional_accuracy": 0.5189170379909718, "finite_ic_date_count": 246.66666666666666, "huber_loss": 0.004111597345940296, "mae": 0.07460264020365888, "mean_daily_ic": 0.03454244447678172, "median_absolute_error": 0.050144435379949524, "median_daily_ic": 0.029849221320966925, "nonfinite_ic_date_count": 0.0, "pearson": 0.07777828498939864, "population_eligible_date_count": 247.33333333333334, "positive_ic_fraction": 0.5782848151062155, "quantile_spread": 0.006675507068565127, "r2": -0.03202184166557661, "rmse": 0.11999341034479567, "spearman": 0.10832935447186648, "trimmed_rmse": 0.11999341034479567, "validation_date_count": 247.33333333333334}` | `{"constant_prediction_date_count": 0.9428090415820634, "constant_target_date_count": 0.0, "daily_ic_std": 0.013322489163091769, "directional_accuracy": 0.03264750863537863, "finite_ic_date_count": 0.9428090415820634, "huber_loss": 0.0003967483598685911, "mae": 0.00416382704910411, "mean_daily_ic": 0.01400983406744851, "median_absolute_error": 0.001151018906056281, "median_daily_ic": 0.01346916078155814, "nonfinite_ic_date_count": 0.0, "pearson": 0.0345636685823174, "population_eligible_date_count": 1.8856180831641267, "positive_ic_fraction": 0.03611460757904787, "quantile_spread": 0.004331056161149291, "r2": 0.03154874122480265, "rmse": 0.015561473096372366, "spearman": 0.05357262249017235, "trimmed_rmse": 0.015561473096372366, "validation_date_count": 1.8856180831641267}` | 147908 |
| `fwd_open_to_close_ret_10s_adj:zero_return_baseline` | `{"constant_prediction_date_count": 247.33333333333334, "constant_target_date_count": 0.0, "directional_accuracy": 0.4955306294434709, "finite_ic_date_count": 0.0, "huber_loss": 0.004038070446781301, "mae": 0.07346328068847664, "median_absolute_error": 0.049050042535573046, "nonfinite_ic_date_count": 0.0, "population_eligible_date_count": 247.33333333333334, "quantile_spread": 8.761854723001186e-05, "r2": -0.023057469193570546, "rmse": 0.11930365921223392, "trimmed_rmse": 0.1193036592122339, "validation_date_count": 247.33333333333334}` | `{"constant_prediction_date_count": 1.8856180831641267, "constant_target_date_count": 0.0, "directional_accuracy": 0.023762482447662336, "finite_ic_date_count": 0.0, "huber_loss": 0.0002864427195259131, "mae": 0.0030492449481568395, "median_absolute_error": 0.0020921905606219354, "nonfinite_ic_date_count": 0.0, "population_eligible_date_count": 1.8856180831641267, "quantile_spread": 0.0033383370845585054, "r2": 0.009117835579838791, "rmse": 0.013834480788097476, "trimmed_rmse": 0.013834480788097481, "validation_date_count": 1.8856180831641267}` | 147908 |
| `fwd_open_to_close_ret_20s_adj:hist_gradient_boosting_cpu` | `{"constant_prediction_date_count": 0.0, "constant_target_date_count": 0.0, "daily_ic_std": 0.09189151077270734, "directional_accuracy": 0.5118642732420973, "finite_ic_date_count": 247.33333333333334, "huber_loss": 0.009401031387400014, "mae": 0.13546618205163088, "mean_daily_ic": 0.04033907585747811, "median_absolute_error": 0.10478943587439433, "median_daily_ic": 0.04621888866647147, "nonfinite_ic_date_count": 0.0, "pearson": 0.03307551419509224, "population_eligible_date_count": 247.33333333333334, "positive_ic_fraction": 0.6736043360433603, "quantile_spread": 0.01302965278953813, "r2": -0.28640909770983297, "rmse": 0.21439786006867223, "spearman": 0.03725366004281502, "trimmed_rmse": 0.21439786006867223, "validation_date_count": 247.33333333333334}` | `{"constant_prediction_date_count": 0.0, "constant_target_date_count": 0.0, "daily_ic_std": 0.005911632256330069, "directional_accuracy": 0.015487342746144323, "finite_ic_date_count": 1.8856180831641267, "huber_loss": 0.0011334366800964286, "mae": 0.013072257032514524, "mean_daily_ic": 0.013661810822581517, "median_absolute_error": 0.02337900475292862, "median_daily_ic": 0.018734399405965864, "nonfinite_ic_date_count": 0.0, "pearson": 0.021698880447462755, "population_eligible_date_count": 1.8856180831641267, "positive_ic_fraction": 0.038377964364146366, "quantile_spread": 0.008319641963186436, "r2": 0.09483724363844412, "rmse": 0.03870263420492124, "spearman": 0.03757400357565388, "trimmed_rmse": 0.03870263420492123, "validation_date_count": 1.8856180831641267}` | 147760 |
| `fwd_open_to_close_ret_20s_adj:lightgbm_cpu` | `{"constant_prediction_date_count": 13.666666666666666, "constant_target_date_count": 0.0, "daily_ic_std": 0.11144305582772686, "directional_accuracy": 0.5242902188726147, "finite_ic_date_count": 205.33333333333334, "huber_loss": 0.007158181767653889, "mae": 0.10957069386716511, "mean_daily_ic": 0.03528038313575018, "median_absolute_error": 0.07324612317691742, "median_daily_ic": 0.03701922047854748, "nonfinite_ic_date_count": 28.333333333333332, "pearson": 0.013953498531235106, "population_eligible_date_count": 247.33333333333334, "positive_ic_fraction": 0.6106910569105691, "quantile_spread": 0.010447198447068215, "r2": -0.05262562569582544, "rmse": 0.1960864061810197, "spearman": -0.005437616565136781, "trimmed_rmse": 0.1960864061810197, "validation_date_count": 247.33333333333334}` | `{"constant_prediction_date_count": 19.3275853524323, "constant_target_date_count": 0.0, "daily_ic_std": 0.007636665182873075, "directional_accuracy": 0.0216668292660883, "finite_ic_date_count": 60.36187170354772, "huber_loss": 0.0009458358216396657, "mae": 0.009748879002269843, "mean_daily_ic": 0.03288857792910645, "median_absolute_error": 0.00256670504900471, "median_daily_ic": 0.038278938025442424, "nonfinite_ic_date_count": 40.069384267237695, "pearson": 0.037380290796213946, "population_eligible_date_count": 1.8856180831641267, "positive_ic_fraction": 0.12498981825587277, "quantile_spread": 0.014379649666872621, "r2": 0.041388355457017204, "rmse": 0.04589688713926874, "spearman": 0.07807322710490239, "trimmed_rmse": 0.04589688713926873, "validation_date_count": 1.8856180831641267}` | 147760 |
| `fwd_open_to_close_ret_20s_adj:ridge_fixed_alpha_1` | `{"constant_prediction_date_count": 0.0, "constant_target_date_count": 0.0, "daily_ic_std": 0.1289593395518916, "directional_accuracy": 0.4880457020748801, "finite_ic_date_count": 247.33333333333334, "huber_loss": 0.007165864484975676, "mae": 0.10985066718162406, "mean_daily_ic": -0.05792753238667861, "median_absolute_error": 0.07439795431744704, "median_daily_ic": -0.05349818050077739, "nonfinite_ic_date_count": 0.0, "pearson": -0.09994480884280961, "population_eligible_date_count": 247.33333333333334, "positive_ic_fraction": 0.3038807588075881, "quantile_spread": -0.00428199185759832, "r2": -0.1330462827392318, "rmse": 0.2047229028017112, "spearman": -0.08743500345894002, "trimmed_rmse": 0.2047229028017112, "validation_date_count": 247.33333333333334}` | `{"constant_prediction_date_count": 0.0, "constant_target_date_count": 0.0, "daily_ic_std": 0.01842560078467293, "directional_accuracy": 0.017436505194215378, "finite_ic_date_count": 1.8856180831641267, "huber_loss": 0.0006618043934367048, "mae": 0.006351255723639133, "mean_daily_ic": 0.0322073851440273, "median_absolute_error": 0.0020628760408609053, "median_daily_ic": 0.02837408744936825, "nonfinite_ic_date_count": 0.0, "pearson": 0.096116756094782, "population_eligible_date_count": 1.8856180831641267, "positive_ic_fraction": 0.1108062062768868, "quantile_spread": 0.007787049457052013, "r2": 0.12474944182626217, "rmse": 0.055800389724306704, "spearman": 0.014040575185610676, "trimmed_rmse": 0.055800389724306704, "validation_date_count": 1.8856180831641267}` | 147760 |
| `fwd_open_to_close_ret_20s_adj:training_mean_baseline` | `{"constant_prediction_date_count": 79.0, "constant_target_date_count": 0.0, "directional_accuracy": 0.5344995726246556, "finite_ic_date_count": 0.0, "huber_loss": 0.006857747484121654, "mae": 0.10638819880390478, "median_absolute_error": 0.07183656809985171, "nonfinite_ic_date_count": 168.33333333333334, "pearson": null, "population_eligible_date_count": 247.33333333333334, "quantile_spread": 0.0003289718194339792, "r2": -0.02537781326483716, "rmse": 0.19276775678284186, "spearman": null, "trimmed_rmse": 0.19276775678284186, "validation_date_count": 247.33333333333334}` | `{"constant_prediction_date_count": 25.39028685672272, "constant_target_date_count": 0.0, "directional_accuracy": 0.01679763219189864, "finite_ic_date_count": 0.0, "huber_loss": 0.0005360362144575309, "mae": 0.005549798201941217, "median_absolute_error": 0.0014510835936342148, "nonfinite_ic_date_count": 27.182510717166817, "pearson": null, "population_eligible_date_count": 1.8856180831641267, "quantile_spread": 0.007457412592612893, "r2": 0.022581144223393926, "rmse": 0.041134399794770946, "spearman": null, "trimmed_rmse": 0.04113439979477096, "validation_date_count": 1.8856180831641267}` | 147760 |
| `fwd_open_to_close_ret_20s_adj:xgboost_gpu` | `{"constant_prediction_date_count": 10.333333333333334, "constant_target_date_count": 0.0, "daily_ic_std": 0.11287353050377251, "directional_accuracy": 0.5246785639793384, "finite_ic_date_count": 237.0, "huber_loss": 0.007129681881924224, "mae": 0.10924163083898265, "mean_daily_ic": 0.024430858267303193, "median_absolute_error": 0.07303482739716328, "median_daily_ic": 0.029186749071923368, "nonfinite_ic_date_count": 0.0, "pearson": 0.01609085377222557, "population_eligible_date_count": 247.33333333333334, "positive_ic_fraction": 0.5912870772543343, "quantile_spread": 0.014627059394097993, "r2": -0.050520859304791076, "rmse": 0.19583204425579623, "spearman": 0.01650679334242722, "trimmed_rmse": 0.19583204425579623, "validation_date_count": 247.33333333333334}` | `{"constant_prediction_date_count": 14.613540144521982, "constant_target_date_count": 0.0, "daily_ic_std": 0.011649101627091868, "directional_accuracy": 0.021345172273683204, "finite_ic_date_count": 12.727922061357855, "huber_loss": 0.0009058179812346662, "mae": 0.009306778076047613, "mean_daily_ic": 0.019676309327483675, "median_absolute_error": 0.002263106262390727, "median_daily_ic": 0.027249051479917404, "nonfinite_ic_date_count": 0.0, "pearson": 0.026046441685701614, "population_eligible_date_count": 1.8856180831641267, "positive_ic_fraction": 0.09272051676229998, "quantile_spread": 0.011061159728877343, "r2": 0.03871015342023631, "rmse": 0.045522062137797026, "spearman": 0.0471798175571618, "trimmed_rmse": 0.045522062137797026, "validation_date_count": 1.8856180831641267}` | 147760 |
| `fwd_open_to_close_ret_20s_adj:zero_return_baseline` | `{"constant_prediction_date_count": 247.33333333333334, "constant_target_date_count": 0.0, "directional_accuracy": 0.4655004273753444, "finite_ic_date_count": 0.0, "huber_loss": 0.006891868254305035, "mae": 0.10622321450431042, "median_absolute_error": 0.06968466295343166, "nonfinite_ic_date_count": 0.0, "population_eligible_date_count": 247.33333333333334, "quantile_spread": 0.0003289718194339792, "r2": -0.04505187859611922, "rmse": 0.1945840732641444, "trimmed_rmse": 0.1945840732641444, "validation_date_count": 247.33333333333334}` | `{"constant_prediction_date_count": 1.8856180831641267, "constant_target_date_count": 0.0, "directional_accuracy": 0.01679763219189864, "finite_ic_date_count": 0.0, "huber_loss": 0.0005551734304491046, "mae": 0.005775208355891512, "median_absolute_error": 0.002889871018963562, "nonfinite_ic_date_count": 0.0, "population_eligible_date_count": 1.8856180831641267, "quantile_spread": 0.007457412592612893, "r2": 0.019935211645503614, "rmse": 0.04131937949922609, "trimmed_rmse": 0.04131937949922608, "validation_date_count": 1.8856180831641267}` | 147760 |
| `fwd_open_to_close_ret_5s_adj:hist_gradient_boosting_cpu` | `{"constant_prediction_date_count": 0.0, "constant_target_date_count": 0.0, "daily_ic_std": 0.11674086996252031, "directional_accuracy": 0.5180064795641443, "finite_ic_date_count": 247.33333333333334, "huber_loss": 0.002613283155616746, "mae": 0.056886771452514785, "mean_daily_ic": 0.049160251915452126, "median_absolute_error": 0.0408419885385578, "median_daily_ic": 0.045550595605817736, "nonfinite_ic_date_count": 0.0, "pearson": 0.09112770579845293, "population_eligible_date_count": 247.33333333333334, "positive_ic_fraction": 0.6559024390243903, "quantile_spread": 0.007826128144380504, "r2": -0.05777517628884721, "rmse": 0.08380520679025306, "spearman": 0.09357477682785148, "trimmed_rmse": 0.08380520679025306, "validation_date_count": 247.33333333333334}` | `{"constant_prediction_date_count": 0.0, "constant_target_date_count": 0.0, "daily_ic_std": 0.009443495036518635, "directional_accuracy": 0.023887816237922972, "finite_ic_date_count": 1.8856180831641267, "huber_loss": 0.0002499214765831236, "mae": 0.00356707496695202, "mean_daily_ic": 0.015552187463152099, "median_absolute_error": 0.004243072703849819, "median_daily_ic": 0.015820346280898075, "nonfinite_ic_date_count": 0.0, "pearson": 0.011942630774092897, "population_eligible_date_count": 1.8856180831641267, "positive_ic_fraction": 0.058573809302694624, "quantile_spread": 0.0019082584918155465, "r2": 0.02656408202891135, "rmse": 0.007535412925967851, "spearman": 0.012661519825546464, "trimmed_rmse": 0.007535412925967857, "validation_date_count": 1.8856180831641267}` | 148013 |
| `fwd_open_to_close_ret_5s_adj:lightgbm_cpu` | `{"constant_prediction_date_count": 31.333333333333332, "constant_target_date_count": 0.0, "daily_ic_std": 0.10221055407414766, "directional_accuracy": 0.5066314180737321, "finite_ic_date_count": 165.0, "huber_loss": 0.0024415330124730496, "mae": 0.05334571242479751, "mean_daily_ic": 0.023847781541373028, "median_absolute_error": 0.03582639545588865, "median_daily_ic": 0.025486384338382583, "nonfinite_ic_date_count": 51.0, "pearson": 0.060561721169615786, "population_eligible_date_count": 247.33333333333334, "positive_ic_fraction": 0.5767059458359057, "quantile_spread": 0.0024893307561956114, "r2": -0.01311737276605581, "rmse": 0.0820364954576966, "spearman": 0.02939181244556612, "trimmed_rmse": 0.0820364954576966, "validation_date_count": 247.33333333333334}` | `{"constant_prediction_date_count": 22.29100466306732, "constant_target_date_count": 0.0, "daily_ic_std": 0.016121995456827833, "directional_accuracy": 0.03960738729696392, "finite_ic_date_count": 74.05853540724841, "huber_loss": 0.00020606763307375072, "mae": 0.0021715718849804094, "mean_daily_ic": 0.02057395370629986, "median_absolute_error": 0.0007449542320562828, "median_daily_ic": 0.014180457397736015, "nonfinite_ic_date_count": 62.487332049517576, "pearson": 0.026834348685620714, "population_eligible_date_count": 1.8856180831641267, "positive_ic_fraction": 0.05308591370046616, "quantile_spread": 0.003862879629938226, "r2": 0.012778919895607147, "rmse": 0.007555523807964761, "spearman": 0.03790233522176004, "trimmed_rmse": 0.007555523807964761, "validation_date_count": 1.8856180831641267}` | 148013 |
| `fwd_open_to_close_ret_5s_adj:ridge_fixed_alpha_1` | `{"constant_prediction_date_count": 0.0, "constant_target_date_count": 0.0, "daily_ic_std": 0.11600895307658211, "directional_accuracy": 0.47135547847245246, "finite_ic_date_count": 247.33333333333334, "huber_loss": 0.0024803137544240988, "mae": 0.053864004086718785, "mean_daily_ic": -0.03102953896143643, "median_absolute_error": 0.03624218442704773, "median_daily_ic": -0.04279959573499021, "nonfinite_ic_date_count": 0.0, "pearson": 0.0016189257563235292, "population_eligible_date_count": 247.33333333333334, "positive_ic_fraction": 0.38063956639566393, "quantile_spread": -0.001022092776230963, "r2": -0.08612684569544464, "rmse": 0.08504932504573749, "spearman": -0.06510136302094954, "trimmed_rmse": 0.08504932504573749, "validation_date_count": 247.33333333333334}` | `{"constant_prediction_date_count": 0.0, "constant_target_date_count": 0.0, "daily_ic_std": 0.0038467872186201332, "directional_accuracy": 0.02918310248280871, "finite_ic_date_count": 1.8856180831641267, "huber_loss": 0.00019410868931265946, "mae": 0.0018712444753327005, "mean_daily_ic": 0.028645375785006963, "median_absolute_error": 0.0012676939924348401, "median_daily_ic": 0.036394155288326416, "nonfinite_ic_date_count": 0.0, "pearson": 0.03097464976026046, "population_eligible_date_count": 1.8856180831641267, "positive_ic_fraction": 0.08127930483341039, "quantile_spread": 0.0015809382695667288, "r2": 0.09085891809799843, "rmse": 0.010288604729038562, "spearman": 0.01646793290753885, "trimmed_rmse": 0.010288604729038562, "validation_date_count": 1.8856180831641267}` | 148013 |
| `fwd_open_to_close_ret_5s_adj:training_mean_baseline` | `{"constant_prediction_date_count": 67.33333333333333, "constant_target_date_count": 0.0, "directional_accuracy": 0.4715017998191389, "finite_ic_date_count": 0.0, "huber_loss": 0.0024291929451910692, "mae": 0.053189311647408, "median_absolute_error": 0.035855185243666, "nonfinite_ic_date_count": 180.0, "pearson": null, "population_eligible_date_count": 247.33333333333334, "quantile_spread": 6.041570408982712e-05, "r2": -0.0073145224444886026, "rmse": 0.08176397668407397, "spearman": null, "trimmed_rmse": 0.08176397668407397, "validation_date_count": 247.33333333333334}` | `{"constant_prediction_date_count": 48.45157949495099, "constant_target_date_count": 0.0, "directional_accuracy": 0.015633898244571624, "finite_ic_date_count": 0.0, "huber_loss": 0.00018500058666204397, "mae": 0.001982935579933888, "median_absolute_error": 0.0009752374040289578, "nonfinite_ic_date_count": 47.86090958879351, "pearson": null, "population_eligible_date_count": 1.8856180831641267, "quantile_spread": 0.0014347839589636294, "r2": 0.005917786676810769, "rmse": 0.0070851376172996385, "spearman": null, "trimmed_rmse": 0.007085137617299645, "validation_date_count": 1.8856180831641267}` | 148013 |
| `fwd_open_to_close_ret_5s_adj:xgboost_gpu` | `{"constant_prediction_date_count": 0.0, "constant_target_date_count": 0.0, "daily_ic_std": 0.10177931208204194, "directional_accuracy": 0.5055201048015313, "finite_ic_date_count": 247.33333333333334, "huber_loss": 0.0024427101606926825, "mae": 0.05331022620543876, "mean_daily_ic": 0.028010701586508577, "median_absolute_error": 0.03573601738205815, "median_daily_ic": 0.029843029596592338, "nonfinite_ic_date_count": 0.0, "pearson": 0.0912243195415403, "population_eligible_date_count": 247.33333333333334, "positive_ic_fraction": 0.6028943089430895, "quantile_spread": 0.005944356884695397, "r2": -0.014700817553918166, "rmse": 0.08210325788527296, "spearman": 0.09877258591549205, "trimmed_rmse": 0.08210325788527296, "validation_date_count": 247.33333333333334}` | `{"constant_prediction_date_count": 0.0, "constant_target_date_count": 0.0, "daily_ic_std": 0.01572993574846483, "directional_accuracy": 0.03858033284572953, "finite_ic_date_count": 1.8856180831641267, "huber_loss": 0.0002086242047538173, "mae": 0.0022268198939862944, "mean_daily_ic": 0.025798727172879298, "median_absolute_error": 0.0008463443312489448, "median_daily_ic": 0.028773578347965165, "nonfinite_ic_date_count": 0.0, "pearson": 0.016701524067826056, "population_eligible_date_count": 1.8856180831641267, "positive_ic_fraction": 0.10060188751360558, "quantile_spread": 0.0021647287803121763, "r2": 0.014844438128432908, "rmse": 0.007606136067300506, "spearman": 0.019870828960984518, "trimmed_rmse": 0.007606136067300506, "validation_date_count": 1.8856180831641267}` | 148013 |
| `fwd_open_to_close_ret_5s_adj:zero_return_baseline` | `{"constant_prediction_date_count": 247.33333333333334, "constant_target_date_count": 0.0, "directional_accuracy": 0.5211268681500165, "finite_ic_date_count": 0.0, "huber_loss": 0.002426999393194972, "mae": 0.0530313718936391, "median_absolute_error": 0.0355566669853119, "nonfinite_ic_date_count": 0.0, "population_eligible_date_count": 247.33333333333334, "quantile_spread": 6.041570408982712e-05, "r2": -0.009041474532511584, "rmse": 0.08183944231936213, "trimmed_rmse": 0.08183944231936212, "validation_date_count": 247.33333333333334}` | `{"constant_prediction_date_count": 1.8856180831641267, "constant_target_date_count": 0.0, "directional_accuracy": 0.024702664432037735, "finite_ic_date_count": 0.0, "huber_loss": 0.0001857384169565214, "mae": 0.001973483250910751, "median_absolute_error": 0.0012512139742705444, "nonfinite_ic_date_count": 0.0, "population_eligible_date_count": 1.8856180831641267, "quantile_spread": 0.0014347839589636294, "r2": 0.004697437420557924, "rmse": 0.007147834472357537, "trimmed_rmse": 0.0071478344723575355, "validation_date_count": 1.8856180831641267}` | 148013 |
| `up_10s:hist_gradient_boosting_cpu` | `{"balanced_accuracy": 0.5396069282368509, "brier": 0.292999271700338, "f1": 0.4920107809628651, "log_loss": 0.811275674905236, "pr_auc": 0.546460833149829, "precision": 0.5717784179042206, "prevalence": 0.5044693705565291, "recall": 0.5323527228040782, "roc_auc": 0.5491295404869644}` | `{"balanced_accuracy": 0.014725992810978115, "brier": 0.04310596954865823, "f1": 0.14333046508578962, "log_loss": 0.12379534403050141, "pr_auc": 0.02700128139534406, "precision": 0.05618101245767904, "prevalence": 0.02376248244766233, "recall": 0.2969487240090828, "roc_auc": 0.019590371855666613}` | 147908 |
| `up_10s:lightgbm_cpu` | `{"balanced_accuracy": 0.511060004879906, "brier": 0.25854378762069624, "f1": 0.09237593211622525, "log_loss": 0.7122412118239413, "pr_auc": 0.524691314943949, "precision": 0.20331069609507638, "prevalence": 0.5044693705565291, "recall": 0.059765430044917654, "roc_auc": 0.5191685832141045}` | `{"balanced_accuracy": 0.01564120890107567, "brier": 0.00946122102908675, "f1": 0.13063929603562213, "log_loss": 0.021684735303841653, "pr_auc": 0.0308301937095972, "precision": 0.2875247437931717, "prevalence": 0.02376248244766233, "recall": 0.084521081730583, "roc_auc": 0.011111950302873081}` | 147908 |
| `up_10s:logistic_fixed_c_1` | `{"balanced_accuracy": 0.4835688853472752, "brier": 0.2580036699150834, "f1": 0.2006279964039055, "log_loss": 0.7138618937082347, "pr_auc": 0.4909338507798278, "precision": 0.48078625889782817, "prevalence": 0.5044693705565291, "recall": 0.18148145777793745, "roc_auc": 0.4771171179347162}` | `{"balanced_accuracy": 0.022216236164546526, "brier": 0.004286279166274664, "f1": 0.20303233983973, "log_loss": 0.011215669243439582, "pr_auc": 0.011958905986244509, "precision": 0.010483297757928792, "prevalence": 0.02376248244766233, "recall": 0.213690718362664, "roc_auc": 0.021397449693498043}` | 147908 |
| `up_10s:majority_class_baseline` | `{"balanced_accuracy": 0.5, "brier": 0.5044693705555201, "f1": 0.0, "log_loss": 13.939003830187131, "pr_auc": 0.5044693705565291, "precision": 0.0, "prevalence": 0.5044693705565291, "recall": 0.0, "roc_auc": 0.5}` | `{"balanced_accuracy": 0.0, "brier": 0.023762482447614797, "f1": 0.0, "log_loss": 0.6565816542782156, "pr_auc": 0.02376248244766233, "precision": 0.0, "prevalence": 0.02376248244766233, "recall": 0.0, "roc_auc": 0.0}` | 147908 |
| `up_10s:training_prevalence_baseline` | `{"balanced_accuracy": 0.5, "brier": 0.2518066276887377, "f1": 0.0, "log_loss": 0.6967720316881777, "pr_auc": 0.5044693705565291, "precision": 0.0, "prevalence": 0.5044693705565291, "recall": 0.0, "roc_auc": 0.5}` | `{"balanced_accuracy": 0.0, "brier": 0.002466366917704261, "f1": 0.0, "log_loss": 0.004947883446512101, "pr_auc": 0.02376248244766233, "precision": 0.0, "prevalence": 0.02376248244766233, "recall": 0.0, "roc_auc": 0.0}` | 147908 |
| `up_10s:xgboost_gpu` | `{"balanced_accuracy": 0.5114187117253557, "brier": 0.2584752669844687, "f1": 0.09800035651745363, "log_loss": 0.7123262015072775, "pr_auc": 0.5423655855214431, "precision": 0.20111900150634818, "prevalence": 0.5044693705565291, "recall": 0.06478400709809794, "roc_auc": 0.5433411098797306}` | `{"balanced_accuracy": 0.016148496986826702, "brier": 0.009418737083102343, "f1": 0.13859343330438145, "log_loss": 0.021901732035522866, "pr_auc": 0.041833580047667844, "precision": 0.2844252195812125, "prevalence": 0.02376248244766233, "recall": 0.09161842146300496, "roc_auc": 0.02135232921569026}` | 147908 |
| `up_20s:hist_gradient_boosting_cpu` | `{"balanced_accuracy": 0.5185534156806159, "brier": 0.3043718455346471, "f1": 0.44454479635569316, "log_loss": 0.8329095197482372, "pr_auc": 0.5591768326162537, "precision": 0.5757992176214465, "prevalence": 0.5344995726246556, "recall": 0.4604772577499148, "roc_auc": 0.5256396327440398}` | `{"balanced_accuracy": 0.011334397775399045, "brier": 0.01684742472802989, "f1": 0.16479172967385808, "log_loss": 0.04994493784460655, "pr_auc": 0.006432334971867897, "precision": 0.048459533888259174, "prevalence": 0.01679763219189864, "recall": 0.31484578183999495, "roc_auc": 0.027701475803624854}` | 147760 |
| `up_20s:lightgbm_cpu` | `{"balanced_accuracy": 0.508306405635587, "brier": 0.25848686635932955, "f1": 0.0789057508823745, "log_loss": 0.7108110573559682, "pr_auc": 0.5470859244709311, "precision": 0.2123210461052869, "prevalence": 0.5344995726246556, "recall": 0.04845701642676134, "roc_auc": 0.5030005501750319}` | `{"balanced_accuracy": 0.011747031504419558, "brier": 0.008160974793462231, "f1": 0.11158958304708683, "log_loss": 0.017226449015763024, "pr_auc": 0.017227854070366064, "precision": 0.30026730297933996, "prevalence": 0.01679763219189864, "recall": 0.06852856982286173, "roc_auc": 0.020832065265070133}` | 147760 |
| `up_20s:logistic_fixed_c_1` | `{"balanced_accuracy": 0.48680155724031543, "brier": 0.26105233697864133, "f1": 0.23749850548277837, "log_loss": 0.7206083201356771, "pr_auc": 0.5282131047658293, "precision": 0.5005040068291507, "prevalence": 0.5344995726246556, "recall": 0.21547408583181538, "roc_auc": 0.48839787808103674}` | `{"balanced_accuracy": 0.01419528732882164, "brier": 0.006007866675135466, "f1": 0.2146426951849376, "log_loss": 0.018244901935234956, "pr_auc": 0.016812262987966748, "precision": 0.018061595408241336, "prevalence": 0.01679763219189864, "recall": 0.23507849560427782, "roc_auc": 0.007715795214003307}` | 147760 |
| `up_20s:majority_class_baseline` | `{"balanced_accuracy": 0.5, "brier": 0.5344995726235866, "f1": 0.0, "log_loss": 14.768768977647108, "pr_auc": 0.5344995726246556, "precision": 0.0, "prevalence": 0.5344995726246556, "recall": 0.0, "roc_auc": 0.5}` | `{"balanced_accuracy": 0.0, "brier": 0.01679763219186507, "f1": 0.0, "log_loss": 0.4641357297919366, "pr_auc": 0.01679763219189864, "precision": 0.0, "prevalence": 0.01679763219189864, "recall": 0.0, "roc_auc": 0.0}` | 147760 |
| `up_20s:training_prevalence_baseline` | `{"balanced_accuracy": 0.5, "brier": 0.2530915738937915, "f1": 0.0, "log_loss": 0.6993448595893931, "pr_auc": 0.5344995726246556, "precision": 0.0, "prevalence": 0.5344995726246556, "recall": 0.0, "roc_auc": 0.5}` | `{"balanced_accuracy": 0.0, "brier": 0.002684766223939368, "f1": 0.0, "log_loss": 0.005387049861439083, "pr_auc": 0.01679763219189864, "precision": 0.0, "prevalence": 0.01679763219189864, "recall": 0.0, "roc_auc": 0.0}` | 147760 |
| `up_20s:xgboost_gpu` | `{"balanced_accuracy": 0.5226856984487096, "brier": 0.25958464482862054, "f1": 0.30542428050017123, "log_loss": 0.7134991137055886, "pr_auc": 0.558130981240846, "precision": 0.3922976696243596, "prevalence": 0.5344995726246556, "recall": 0.3225267171982214, "roc_auc": 0.5257548220354459}` | `{"balanced_accuracy": 0.016299041770906995, "brier": 0.009752828223442481, "f1": 0.26254140363809003, "log_loss": 0.021097586263097805, "pr_auc": 0.01608731906683722, "precision": 0.2804054643579329, "prevalence": 0.01679763219189864, "recall": 0.3396839605661486, "roc_auc": 0.014309419972728325}` | 147760 |
| `up_5s:hist_gradient_boosting_cpu` | `{"balanced_accuracy": 0.5359850250882549, "brier": 0.258166804937382, "f1": 0.4511553384086601, "log_loss": 0.7126232926664943, "pr_auc": 0.5277665051613284, "precision": 0.540382663892246, "prevalence": 0.4788731318499834, "recall": 0.45358667513367984, "roc_auc": 0.552393099217168}` | `{"balanced_accuracy": 0.0028387057679093615, "brier": 0.003101304124466634, "f1": 0.12602020651718798, "log_loss": 0.007348100151123535, "pr_auc": 0.024327146455644225, "precision": 0.04651120538741109, "prevalence": 0.024702664432037755, "recall": 0.22217848225521575, "roc_auc": 0.004290826139751513}` | 148013 |
| `up_5s:lightgbm_cpu` | `{"balanced_accuracy": 0.5090831321244326, "brier": 0.2526584906775257, "f1": 0.08751393534002229, "log_loss": 0.6990945405890406, "pr_auc": 0.5021924580461001, "precision": 0.19010946430301268, "prevalence": 0.4788731318499834, "recall": 0.05683957482549889, "roc_auc": 0.5245009855702704}` | `{"balanced_accuracy": 0.01284548863919923, "brier": 0.0038152608698681697, "f1": 0.12376339425450164, "log_loss": 0.00835349763959382, "pr_auc": 0.0315898499306218, "precision": 0.26885538275280435, "prevalence": 0.024702664432037755, "recall": 0.08038329759774086, "roc_auc": 0.016854016907610046}` | 148013 |
| `up_5s:logistic_fixed_c_1` | `{"balanced_accuracy": 0.493070737997139, "brier": 0.2534856023244856, "f1": 0.16520367561153365, "log_loss": 0.7012286565095306, "pr_auc": 0.4766680563964993, "precision": 0.4840680199343943, "prevalence": 0.4788731318499834, "recall": 0.13823840723056366, "roc_auc": 0.48779381490086954}` | `{"balanced_accuracy": 0.01088041775481031, "brier": 0.004067301924251551, "f1": 0.18288254290471873, "log_loss": 0.008538145497536164, "pr_auc": 0.017268935647560796, "precision": 0.00747309370919764, "prevalence": 0.024702664432037755, "recall": 0.16910719517015957, "roc_auc": 0.021382452116923432}` | 148013 |
| `up_5s:majority_class_baseline` | `{"balanced_accuracy": 0.5, "brier": 0.47887313184902575, "f1": 0.0, "log_loss": 13.231753617998246, "pr_auc": 0.4788731318499834, "precision": 0.0, "prevalence": 0.4788731318499834, "recall": 0.0, "roc_auc": 0.5}` | `{"balanced_accuracy": 0.0, "brier": 0.02470266443198836, "f1": 0.0, "log_loss": 0.6825598425413064, "pr_auc": 0.024702664432037755, "precision": 0.0, "prevalence": 0.024702664432037755, "recall": 0.0, "roc_auc": 0.0}` | 148013 |
| `up_5s:training_prevalence_baseline` | `{"balanced_accuracy": 0.5, "brier": 0.2503159897289371, "f1": 0.0, "log_loss": 0.6937887568637278, "pr_auc": 0.4788731318499834, "precision": 0.0, "prevalence": 0.4788731318499834, "recall": 0.0, "roc_auc": 0.5}` | `{"balanced_accuracy": 0.0, "brier": 0.0024392275991128435, "f1": 0.0, "log_loss": 0.004894902808114264, "pr_auc": 0.024702664432037755, "precision": 0.0, "prevalence": 0.024702664432037755, "recall": 0.0, "roc_auc": 0.0}` | 148013 |
| `up_5s:xgboost_gpu` | `{"balanced_accuracy": 0.5100989088452335, "brier": 0.25348724446334797, "f1": 0.09432605569355472, "log_loss": 0.7012246061706343, "pr_auc": 0.5196012688066332, "precision": 0.19041963578780682, "prevalence": 0.4788731318499834, "recall": 0.0626900686419324, "roc_auc": 0.5517482121800915}` | `{"balanced_accuracy": 0.014282013854098765, "brier": 0.0048953875256443945, "f1": 0.13339718724698496, "log_loss": 0.011182250339420642, "pr_auc": 0.03307167561694154, "precision": 0.26929403147326153, "prevalence": 0.024702664432037755, "recall": 0.0886571452995211, "roc_auc": 0.015485238586588828}` | 148013 |

## Finite daily IC coverage

Undefined same-date IC is excluded, never coerced to zero.

| Target/fold/model | Validation dates | Population eligible | Finite IC | Constant prediction | Constant target | Non-finite IC |
|---|---:|---:|---:|---:|---:|---:|
| `fwd_open_to_close_ret_10s_adj:fold_2023:hist_gradient_boosting_cpu` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_10s_adj:fold_2023:lightgbm_cpu` | 246 | 246 | 185 | 10 | 0 | 51 |
| `fwd_open_to_close_ret_10s_adj:fold_2023:ridge_fixed_alpha_1` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_10s_adj:fold_2023:training_mean_baseline` | 246 | 246 | 0 | 126 | 0 | 120 |
| `fwd_open_to_close_ret_10s_adj:fold_2023:xgboost_gpu` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_10s_adj:fold_2023:zero_return_baseline` | 246 | 246 | 0 | 246 | 0 | 0 |
| `fwd_open_to_close_ret_10s_adj:fold_2024:hist_gradient_boosting_cpu` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_10s_adj:fold_2024:lightgbm_cpu` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_10s_adj:fold_2024:ridge_fixed_alpha_1` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_10s_adj:fold_2024:training_mean_baseline` | 246 | 246 | 0 | 54 | 0 | 192 |
| `fwd_open_to_close_ret_10s_adj:fold_2024:xgboost_gpu` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_10s_adj:fold_2024:zero_return_baseline` | 246 | 246 | 0 | 246 | 0 | 0 |
| `fwd_open_to_close_ret_10s_adj:fold_2025:hist_gradient_boosting_cpu` | 250 | 250 | 250 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_10s_adj:fold_2025:lightgbm_cpu` | 250 | 250 | 218 | 0 | 0 | 32 |
| `fwd_open_to_close_ret_10s_adj:fold_2025:ridge_fixed_alpha_1` | 250 | 250 | 250 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_10s_adj:fold_2025:training_mean_baseline` | 250 | 250 | 0 | 0 | 0 | 250 |
| `fwd_open_to_close_ret_10s_adj:fold_2025:xgboost_gpu` | 250 | 250 | 248 | 2 | 0 | 0 |
| `fwd_open_to_close_ret_10s_adj:fold_2025:zero_return_baseline` | 250 | 250 | 0 | 250 | 0 | 0 |
| `fwd_open_to_close_ret_20s_adj:fold_2023:hist_gradient_boosting_cpu` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_20s_adj:fold_2023:lightgbm_cpu` | 246 | 246 | 120 | 41 | 0 | 85 |
| `fwd_open_to_close_ret_20s_adj:fold_2023:ridge_fixed_alpha_1` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_20s_adj:fold_2023:training_mean_baseline` | 246 | 246 | 0 | 86 | 0 | 160 |
| `fwd_open_to_close_ret_20s_adj:fold_2023:xgboost_gpu` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_20s_adj:fold_2023:zero_return_baseline` | 246 | 246 | 0 | 246 | 0 | 0 |
| `fwd_open_to_close_ret_20s_adj:fold_2024:hist_gradient_boosting_cpu` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_20s_adj:fold_2024:lightgbm_cpu` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_20s_adj:fold_2024:ridge_fixed_alpha_1` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_20s_adj:fold_2024:training_mean_baseline` | 246 | 246 | 0 | 106 | 0 | 140 |
| `fwd_open_to_close_ret_20s_adj:fold_2024:xgboost_gpu` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_20s_adj:fold_2024:zero_return_baseline` | 246 | 246 | 0 | 246 | 0 | 0 |
| `fwd_open_to_close_ret_20s_adj:fold_2025:hist_gradient_boosting_cpu` | 250 | 250 | 250 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_20s_adj:fold_2025:lightgbm_cpu` | 250 | 250 | 250 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_20s_adj:fold_2025:ridge_fixed_alpha_1` | 250 | 250 | 250 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_20s_adj:fold_2025:training_mean_baseline` | 250 | 250 | 0 | 45 | 0 | 205 |
| `fwd_open_to_close_ret_20s_adj:fold_2025:xgboost_gpu` | 250 | 250 | 219 | 31 | 0 | 0 |
| `fwd_open_to_close_ret_20s_adj:fold_2025:zero_return_baseline` | 250 | 250 | 0 | 250 | 0 | 0 |
| `fwd_open_to_close_ret_5s_adj:fold_2023:hist_gradient_boosting_cpu` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_5s_adj:fold_2023:lightgbm_cpu` | 246 | 246 | 182 | 50 | 0 | 14 |
| `fwd_open_to_close_ret_5s_adj:fold_2023:ridge_fixed_alpha_1` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_5s_adj:fold_2023:training_mean_baseline` | 246 | 246 | 0 | 0 | 0 | 246 |
| `fwd_open_to_close_ret_5s_adj:fold_2023:xgboost_gpu` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_5s_adj:fold_2023:zero_return_baseline` | 246 | 246 | 0 | 246 | 0 | 0 |
| `fwd_open_to_close_ret_5s_adj:fold_2024:hist_gradient_boosting_cpu` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_5s_adj:fold_2024:lightgbm_cpu` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_5s_adj:fold_2024:ridge_fixed_alpha_1` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_5s_adj:fold_2024:training_mean_baseline` | 246 | 246 | 0 | 112 | 0 | 134 |
| `fwd_open_to_close_ret_5s_adj:fold_2024:xgboost_gpu` | 246 | 246 | 246 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_5s_adj:fold_2024:zero_return_baseline` | 246 | 246 | 0 | 246 | 0 | 0 |
| `fwd_open_to_close_ret_5s_adj:fold_2025:hist_gradient_boosting_cpu` | 250 | 250 | 250 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_5s_adj:fold_2025:lightgbm_cpu` | 250 | 250 | 67 | 44 | 0 | 139 |
| `fwd_open_to_close_ret_5s_adj:fold_2025:ridge_fixed_alpha_1` | 250 | 250 | 250 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_5s_adj:fold_2025:training_mean_baseline` | 250 | 250 | 0 | 90 | 0 | 160 |
| `fwd_open_to_close_ret_5s_adj:fold_2025:xgboost_gpu` | 250 | 250 | 250 | 0 | 0 | 0 |
| `fwd_open_to_close_ret_5s_adj:fold_2025:zero_return_baseline` | 250 | 250 | 0 | 250 | 0 | 0 |

## Selection policy

LightGBM fold 2023 uses the fixed conservative default. Fold 2024 selection uses only fold 2023 evidence; fold 2025 uses only folds 2023–2024. Inner early stopping uses the chronological tail of the outer training period. HistGradientBoosting is fixed; XGBoost GPU is an independent fixed-configuration verification model.

```json
{
  "fwd_open_to_close_ret_10s_adj:fold_2023": {
    "candidate_index": 0,
    "candidate_name": "conservative",
    "evidence_folds": [],
    "inner_boundary": "2022-07-04",
    "rounds": 5
  },
  "fwd_open_to_close_ret_10s_adj:fold_2024": {
    "candidate_index": 0,
    "candidate_name": "conservative",
    "evidence_folds": [
      "fold_2023"
    ],
    "inner_boundary": "2023-05-09",
    "rounds": 287
  },
  "fwd_open_to_close_ret_10s_adj:fold_2025": {
    "candidate_index": 0,
    "candidate_name": "conservative",
    "evidence_folds": [
      "fold_2023",
      "fold_2024"
    ],
    "inner_boundary": "2024-03-11",
    "rounds": 1
  },
  "fwd_open_to_close_ret_20s_adj:fold_2023": {
    "candidate_index": 0,
    "candidate_name": "conservative",
    "evidence_folds": [],
    "inner_boundary": "2022-07-04",
    "rounds": 1
  },
  "fwd_open_to_close_ret_20s_adj:fold_2024": {
    "candidate_index": 0,
    "candidate_name": "conservative",
    "evidence_folds": [
      "fold_2023"
    ],
    "inner_boundary": "2023-05-09",
    "rounds": 68
  },
  "fwd_open_to_close_ret_20s_adj:fold_2025": {
    "candidate_index": 1,
    "candidate_name": "moderate",
    "evidence_folds": [
      "fold_2023",
      "fold_2024"
    ],
    "inner_boundary": "2024-03-11",
    "rounds": 1
  },
  "fwd_open_to_close_ret_5s_adj:fold_2023": {
    "candidate_index": 0,
    "candidate_name": "conservative",
    "evidence_folds": [],
    "inner_boundary": "2022-07-04",
    "rounds": 4
  },
  "fwd_open_to_close_ret_5s_adj:fold_2024": {
    "candidate_index": 0,
    "candidate_name": "conservative",
    "evidence_folds": [
      "fold_2023"
    ],
    "inner_boundary": "2023-05-09",
    "rounds": 129
  },
  "fwd_open_to_close_ret_5s_adj:fold_2025": {
    "candidate_index": 0,
    "candidate_name": "conservative",
    "evidence_folds": [
      "fold_2023",
      "fold_2024"
    ],
    "inner_boundary": "2024-03-11",
    "rounds": 1
  },
  "up_10s:fold_2023": {
    "candidate_index": 0,
    "candidate_name": "conservative",
    "evidence_folds": [],
    "inner_boundary": "2022-07-04",
    "rounds": 3
  },
  "up_10s:fold_2024": {
    "candidate_index": 1,
    "candidate_name": "moderate",
    "evidence_folds": [
      "fold_2023"
    ],
    "inner_boundary": "2023-05-09",
    "rounds": 127
  },
  "up_10s:fold_2025": {
    "candidate_index": 1,
    "candidate_name": "moderate",
    "evidence_folds": [
      "fold_2023",
      "fold_2024"
    ],
    "inner_boundary": "2024-03-11",
    "rounds": 1
  },
  "up_20s:fold_2023": {
    "candidate_index": 0,
    "candidate_name": "conservative",
    "evidence_folds": [],
    "inner_boundary": "2022-07-04",
    "rounds": 1
  },
  "up_20s:fold_2024": {
    "candidate_index": 1,
    "candidate_name": "moderate",
    "evidence_folds": [
      "fold_2023"
    ],
    "inner_boundary": "2023-05-09",
    "rounds": 23
  },
  "up_20s:fold_2025": {
    "candidate_index": 1,
    "candidate_name": "moderate",
    "evidence_folds": [
      "fold_2023",
      "fold_2024"
    ],
    "inner_boundary": "2024-03-11",
    "rounds": 1
  },
  "up_5s:fold_2023": {
    "candidate_index": 0,
    "candidate_name": "conservative",
    "evidence_folds": [],
    "inner_boundary": "2022-07-04",
    "rounds": 1
  },
  "up_5s:fold_2024": {
    "candidate_index": 1,
    "candidate_name": "moderate",
    "evidence_folds": [
      "fold_2023"
    ],
    "inner_boundary": "2023-05-09",
    "rounds": 78
  },
  "up_5s:fold_2025": {
    "candidate_index": 1,
    "candidate_name": "moderate",
    "evidence_folds": [
      "fold_2023",
      "fold_2024"
    ],
    "inner_boundary": "2024-03-11",
    "rounds": 1
  }
}
```

The final 2026 holdout remained locked.
