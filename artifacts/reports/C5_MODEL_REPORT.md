# C5 Linear Baseline Model Report

Model set `linear_baselines_v1` v1; final holdout accessed: **False**.

**Conclusion: Linear signal NOT demonstrated: selected Ridge beats the best naive RMSE baseline on 0/3 tasks; selected Logistic beats prevalence log loss on 0/3 tasks.**

## Scope and interpretation

These are validation-fold reference models, not trading strategies. Metrics are predictive diagnostics only; they contain no costs, execution, portfolio, Sharpe, or profitability analysis. A model that fails naive baselines is an honest negative result.

## Selected hyperparameters

```json
{
  "fwd_open_to_close_ret_10s_adj": {
    "by_fold": {
      "fold_2023": 100.0,
      "fold_2024": 0.01,
      "fold_2025": 100.0
    },
    "mean_grid_scores": {
      "0.01": 0.13751002738859483,
      "0.1": 0.1375100028121643,
      "1.0": 0.13750994454355486,
      "10.0": 0.13752101372347755,
      "100.0": 0.13764153588093528
    },
    "parameter": "alpha",
    "validation_scores_by_fold": {
      "fold_2023": {
        "0.01": 0.10581132101061738,
        "0.1": 0.10581082789543474,
        "1.0": 0.1058059113182162,
        "10.0": 0.10575775861576364,
        "100.0": 0.1053333386623119
      },
      "fold_2024": {
        "0.01": 0.18888376251940533,
        "0.1": 0.1888842121304371,
        "1.0": 0.1888892496438294,
        "10.0": 0.18897302863263252,
        "100.0": 0.1897660614749512
      },
      "fold_2025": {
        "0.01": 0.11783499863576175,
        "0.1": 0.11783496841062106,
        "1.0": 0.11783467266861897,
        "10.0": 0.11783225392203645,
        "100.0": 0.11782520750554275
      }
    }
  },
  "fwd_open_to_close_ret_20s_adj": {
    "by_fold": {
      "fold_2023": 100.0,
      "fold_2024": 0.01,
      "fold_2025": 100.0
    },
    "mean_grid_scores": {
      "0.01": 0.2767371265099689,
      "0.1": 0.27674492526061206,
      "1.0": 0.2768211626476071,
      "10.0": 0.2774433587962523,
      "100.0": 0.2795417212825333
    },
    "parameter": "alpha",
    "validation_scores_by_fold": {
      "fold_2023": {
        "0.01": 0.2071226537256743,
        "0.1": 0.2071223695406683,
        "1.0": 0.20711951732765152,
        "10.0": 0.2070902648353775,
        "100.0": 0.20681001798851478
      },
      "fold_2024": {
        "0.01": 0.44478228602991227,
        "0.1": 0.4448060167848891,
        "1.0": 0.4450380840367553,
        "10.0": 0.4469389206363907,
        "100.0": 0.4535601082737203
      },
      "fold_2025": {
        "0.01": 0.17830643977432017,
        "0.1": 0.17830638945627875,
        "1.0": 0.1783058865784145,
        "10.0": 0.17830089091698875,
        "100.0": 0.17825503758536484
      }
    }
  },
  "fwd_open_to_close_ret_5s_adj": {
    "by_fold": {
      "fold_2023": 100.0,
      "fold_2024": 100.0,
      "fold_2025": 100.0
    },
    "mean_grid_scores": {
      "0.01": 0.09912766352780651,
      "0.1": 0.09911210139042526,
      "1.0": 0.09895894282463248,
      "10.0": 0.09763009931562448,
      "100.0": 0.09155332579796456
    },
    "parameter": "alpha",
    "validation_scores_by_fold": {
      "fold_2023": {
        "0.01": 0.07424756342551407,
        "0.1": 0.07424714646407073,
        "1.0": 0.07424302200731364,
        "10.0": 0.07420520134791682,
        "100.0": 0.07393681564775904
      },
      "fold_2024": {
        "0.01": 0.14041817761540346,
        "0.1": 0.1403719106652705,
        "1.0": 0.1399165841406658,
        "10.0": 0.13596809842631974,
        "100.0": 0.11800776105446226
      },
      "fold_2025": {
        "0.01": 0.08271724954250201,
        "0.1": 0.08271724704193459,
        "1.0": 0.08271722232591804,
        "10.0": 0.0827169981726369,
        "100.0": 0.08271540069167238
      }
    }
  },
  "up_10s": {
    "by_fold": {
      "fold_2023": 0.01,
      "fold_2024": 0.01,
      "fold_2025": 0.01
    },
    "mean_grid_scores": {
      "0.01": 0.7137400355888349,
      "0.1": 0.7146919058020765,
      "1.0": 0.7148091011461086,
      "10.0": 0.7148219230808414
    },
    "parameter": "C",
    "validation_scores_by_fold": {
      "fold_2023": {
        "0.01": 0.7182973260545803,
        "0.1": 0.7203899097632095,
        "1.0": 0.7206845991234375,
        "10.0": 0.7207170550557599
      },
      "fold_2024": {
        "0.01": 0.7246297206389726,
        "0.1": 0.7253622038001131,
        "1.0": 0.7254426127375573,
        "10.0": 0.725447135387434
      },
      "fold_2025": {
        "0.01": 0.6982930600729518,
        "0.1": 0.6983236038429071,
        "1.0": 0.6983000915773313,
        "10.0": 0.6983015787993304
      }
    }
  },
  "up_20s": {
    "by_fold": {
      "fold_2023": 0.01,
      "fold_2024": 0.01,
      "fold_2025": 0.01
    },
    "mean_grid_scores": {
      "0.01": 0.7207084918866539,
      "0.1": 0.7215508542414583,
      "1.0": 0.7216909996941924,
      "10.0": 0.7217061273293369
    },
    "parameter": "C",
    "validation_scores_by_fold": {
      "fold_2023": {
        "0.01": 0.7121260777470116,
        "0.1": 0.7133018448480447,
        "1.0": 0.7135108623340645,
        "10.0": 0.7135346173090729
      },
      "fold_2024": {
        "0.01": 0.7475420877163059,
        "0.1": 0.7487903870051628,
        "1.0": 0.7489836225486914,
        "10.0": 0.749003455222396
      },
      "fold_2025": {
        "0.01": 0.7024573101966441,
        "0.1": 0.7025603308711672,
        "1.0": 0.7025785141998209,
        "10.0": 0.7025803094565422
      }
    }
  },
  "up_5s": {
    "by_fold": {
      "fold_2023": 0.01,
      "fold_2024": 0.01,
      "fold_2025": 0.01
    },
    "mean_grid_scores": {
      "0.01": 0.7012565464317356,
      "0.1": 0.7019395103150453,
      "1.0": 0.7019731043652694,
      "10.0": 0.7020174889977682
    },
    "parameter": "C",
    "validation_scores_by_fold": {
      "fold_2023": {
        "0.01": 0.7098513999488159,
        "0.1": 0.711238413384718,
        "1.0": 0.7114172985820859,
        "10.0": 0.7115404296054689
      },
      "fold_2024": {
        "0.01": 0.7033621830037879,
        "0.1": 0.7039713243249287,
        "1.0": 0.7039261709965382,
        "10.0": 0.7039345413715846
      },
      "fold_2025": {
        "0.01": 0.6905560563426031,
        "0.1": 0.6906087932354895,
        "1.0": 0.6905758435171838,
        "10.0": 0.6905774960162512
      }
    }
  }
}
```

## Fold aggregate metrics

| Task/model | Selected metric means and dispersion |
|---|---|
| `fwd_open_to_close_ret_10s_adj:ridge_fixed_alpha_1` | mean `{"directional_accuracy": 0.4677882905207196, "mae": 0.07549472162483394, "pearson": -0.0918799513496531, "r2": -0.36686369384230216, "rmse": 0.13750994454355486, "spearman": -0.09417908218854636}`; std `{"directional_accuracy": 0.018642782803861706, "mae": 0.0037517352212583337, "pearson": 0.10418144064818523, "r2": 0.43679599206880193, "rmse": 0.03666103762258199, "spearman": 0.019563937987171584}`; n=150,184 |
| `fwd_open_to_close_ret_10s_adj:ridge_selected` | mean `{"directional_accuracy": 0.4677490575795356, "mae": 0.07545985461405258, "pearson": -0.0923372768474557, "r2": -0.3634776654304419, "rmse": 0.13734743622908666, "spearman": -0.09351776146269077}`; std `{"directional_accuracy": 0.01872252201197327, "mae": 0.0037775367352774402, "pearson": 0.10402353551751084, "r2": 0.43875337087470395, "rmse": 0.03679679689344137, "spearman": 0.018986381896247517}`; n=150,184 |
| `fwd_open_to_close_ret_10s_adj:training_mean_baseline` | mean `{"directional_accuracy": 0.5066833006590383, "mae": 0.07315318304398792, "r2": -0.01498052172429635, "rmse": 0.11812569800756341}`; std `{"directional_accuracy": 0.022532052674467697, "mae": 0.002965768213494539, "r2": 0.011951000777594742, "rmse": 0.013474525674013176}`; n=150,184 |
| `fwd_open_to_close_ret_10s_adj:zero_return_baseline` | mean `{"directional_accuracy": 0.4933166993409617, "mae": 0.07289638624079188, "r2": -0.023022618620309965, "rmse": 0.11860817552317383}`; std `{"directional_accuracy": 0.02253205267446773, "mae": 0.003025376639610729, "r2": 0.009068730819331086, "rmse": 0.013638068970203972}`; n=150,184 |
| `fwd_open_to_close_ret_20s_adj:ridge_fixed_alpha_1` | mean `{"directional_accuracy": 0.48771478896652676, "mae": 0.11068282827238352, "pearson": -0.03454788763153794, "r2": -0.7933429962960195, "rmse": 0.2768211626476071, "spearman": -0.08870206586860897}`; std `{"directional_accuracy": 0.019160091037990445, "mae": 0.006799836127527037, "pearson": 0.018328535007849693, "r2": 1.0582638808840703, "rmse": 0.11952755835781274, "spearman": 0.012847622935666823}`; n=150,017 |
| `fwd_open_to_close_ret_20s_adj:ridge_selected` | mean `{"directional_accuracy": 0.48796291017945553, "mae": 0.11065764566935277, "pearson": -0.03548054154192158, "r2": -0.7908258139163564, "rmse": 0.2766157805345973, "spearman": -0.08877520297689517}`; std `{"directional_accuracy": 0.01914083466543332, "mae": 0.006814603886660904, "pearson": 0.018585135217447018, "r2": 1.0573529034984455, "rmse": 0.11948173334401489, "spearman": 0.012827784859561021}`; n=150,017 |
| `fwd_open_to_close_ret_20s_adj:training_mean_baseline` | mean `{"directional_accuracy": 0.5366023631237767, "mae": 0.1062486927254054, "r2": -0.017749240539043216, "rmse": 0.2092517725478725}`; std `{"directional_accuracy": 0.015688518124700193, "mae": 0.004923826959154834, "r2": 0.012399526817199325, "rmse": 0.0291154984492569}`; n=150,017 |
| `fwd_open_to_close_ret_20s_adj:zero_return_baseline` | mean `{"directional_accuracy": 0.46339763687622315, "mae": 0.10612952456542446, "r2": -0.035070515606029806, "rmse": 0.21097697685035507}`; std `{"directional_accuracy": 0.01568851812470017, "mae": 0.005314252459008133, "r2": 0.005783610948206526, "rmse": 0.029013735034428063}`; n=150,017 |
| `fwd_open_to_close_ret_5s_adj:ridge_fixed_alpha_1` | mean `{"directional_accuracy": 0.4702870992130299, "mae": 0.0537413270288137, "pearson": -0.0031981198002309793, "r2": -0.5193019955142671, "rmse": 0.09895894282463248, "spearman": -0.06641397321301762}`; std `{"directional_accuracy": 0.02824119942953455, "mae": 0.0021602645201007713, "pearson": 0.016314780345788735, "r2": 0.6803450581943995, "rmse": 0.029167325376061794, "spearman": 0.01658767132056785}`; n=150,304 |
| `fwd_open_to_close_ret_5s_adj:ridge_selected` | mean `{"directional_accuracy": 0.4702283965457153, "mae": 0.05362197030167687, "pearson": 0.0024572552681804715, "r2": -0.27765986041854607, "rmse": 0.09155332579796456, "spearman": -0.06603702772953711}`; std `{"directional_accuracy": 0.028087323206489774, "mae": 0.0020379286087312603, "pearson": 0.024641636418067568, "r2": 0.3451111788357564, "rmse": 0.019046325059329704, "spearman": 0.01657221058919811}`; n=150,304 |
| `fwd_open_to_close_ret_5s_adj:training_mean_baseline` | mean `{"directional_accuracy": 0.4733310977593397, "mae": 0.052749320438218866, "r2": -0.007309466690629189, "rmse": 0.0812932184491766}`; std `{"directional_accuracy": 0.014776776971414416, "mae": 0.0019071537091310039, "r2": 0.005889501694923101, "rmse": 0.006934337225632174}`; n=150,304 |
| `fwd_open_to_close_ret_5s_adj:zero_return_baseline` | mean `{"directional_accuracy": 0.519025279125743, "mae": 0.05259757472616495, "r2": -0.0090423338521608, "rmse": 0.08136840719047496}`; std `{"directional_accuracy": 0.023824823998770422, "mae": 0.0019149479250849975, "r2": 0.004692713735302148, "rmse": 0.006996858739549896}`; n=150,304 |
| `up_10s:logistic_fixed_c_1` | mean `{"balanced_accuracy": 0.4838418511164799, "brier": 0.25830869080013424, "f1": 0.2014849326939944, "log_loss": 0.7148091011461086, "pr_auc": 0.4939289439575581, "precision": 0.48790609347929714, "prevalence": 0.5066833006590383, "recall": 0.18172649701837285, "roc_auc": 0.4764630554670824}`; std `{"balanced_accuracy": 0.02253213556652217, "brier": 0.0043153327875832025, "f1": 0.20213716244999122, "log_loss": 0.011834137656078563, "pr_auc": 0.009710855598863697, "precision": 0.010716787863465527, "prevalence": 0.022532052674467697, "recall": 0.21289842064058062, "roc_auc": 0.02144108111430043}`; n=150,184 |
| `up_10s:logistic_selected` | mean `{"balanced_accuracy": 0.4831015606794978, "brier": 0.25793296794095294, "f1": 0.20017417394695902, "log_loss": 0.7137400355888349, "pr_auc": 0.49484782701224805, "precision": 0.4865273791789923, "prevalence": 0.5066833006590383, "recall": 0.18139617265444552, "roc_auc": 0.476982426270832}`; std `{"balanced_accuracy": 0.02348828540411492, "brier": 0.003983110223148436, "f1": 0.2028433914036586, "log_loss": 0.011224425589885933, "pr_auc": 0.011284008717874864, "precision": 0.011221443111630251, "prevalence": 0.022532052674467697, "recall": 0.21387343965235098, "roc_auc": 0.019922521357182584}`; n=150,184 |
| `up_10s:majority_class_baseline` | mean `{"balanced_accuracy": 0.5, "brier": 0.5066833006580249, "f1": 0.0, "log_loss": 14.000176979598754, "pr_auc": 0.5066833006590383, "precision": 0.0, "prevalence": 0.5066833006590383, "recall": 0.0, "roc_auc": 0.5}`; std `{"balanced_accuracy": 0.0, "brier": 0.022532052674422636, "f1": 0.0, "log_loss": 0.6225836232334097, "pr_auc": 0.022532052674467697, "precision": 0.0, "prevalence": 0.022532052674467697, "recall": 0.0, "roc_auc": 0.0}`; n=150,184 |
| `up_10s:training_prevalence_baseline` | mean `{"balanced_accuracy": 0.5, "brier": 0.25191896931401175, "f1": 0.0, "log_loss": 0.6969969328600248, "pr_auc": 0.5066833006590383, "precision": 0.0, "prevalence": 0.5066833006590383, "recall": 0.0, "roc_auc": 0.5}`; std `{"balanced_accuracy": 0.0, "brier": 0.0024087365639209137, "f1": 0.0, "log_loss": 0.004832538551278804, "pr_auc": 0.022532052674467697, "precision": 0.0, "prevalence": 0.022532052674467697, "recall": 0.0, "roc_auc": 0.0}`; n=150,184 |
| `up_20s:logistic_fixed_c_1` | mean `{"balanced_accuracy": 0.4871118766012579, "brier": 0.26128508906253606, "f1": 0.23800459830289153, "log_loss": 0.7216909996941924, "pr_auc": 0.5317388886981381, "precision": 0.5066648901632981, "prevalence": 0.5366023631237767, "recall": 0.2155897039788857, "roc_auc": 0.4889358560338861}`; std `{"balanced_accuracy": 0.014540618008885295, "brier": 0.006309584669066689, "f1": 0.2139959500431299, "log_loss": 0.01980815498122803, "pr_auc": 0.014726856111098793, "precision": 0.013525829324761358, "prevalence": 0.015688518124700193, "recall": 0.2345639218814348, "roc_auc": 0.008661193647259226}`; n=150,017 |
| `up_20s:logistic_selected` | mean `{"balanced_accuracy": 0.48610148088460264, "brier": 0.2609598062755589, "f1": 0.23608855421840147, "log_loss": 0.7207084918866539, "pr_auc": 0.5313414664139989, "precision": 0.5085941897786612, "prevalence": 0.5366023631237767, "recall": 0.21481679547943133, "roc_auc": 0.4883260249018608}`; std `{"balanced_accuracy": 0.01637256191491302, "brier": 0.006191894282263298, "f1": 0.21442241100126783, "log_loss": 0.019380448315206723, "pr_auc": 0.014831272735266153, "precision": 0.010960876984812813, "prevalence": 0.015688518124700193, "recall": 0.23535406119293703, "roc_auc": 0.008299579533508242}`; n=150,017 |
| `up_20s:majority_class_baseline` | mean `{"balanced_accuracy": 0.5, "brier": 0.5366023631227037, "f1": 0.0, "log_loss": 14.826871226330697, "pr_auc": 0.5366023631237767, "precision": 0.0, "prevalence": 0.5366023631237767, "recall": 0.0, "roc_auc": 0.5}`; std `{"balanced_accuracy": 0.0, "brier": 0.015688518124668812, "f1": 0.0, "log_loss": 0.4334897755812025, "pr_auc": 0.015688518124700193, "precision": 0.0, "prevalence": 0.015688518124700193, "recall": 0.0, "roc_auc": 0.0}`; n=150,017 |
| `up_20s:training_prevalence_baseline` | mean `{"balanced_accuracy": 0.5, "brier": 0.25316208900231346, "f1": 0.0, "log_loss": 0.6994859678359235, "pr_auc": 0.5366023631237767, "precision": 0.0, "prevalence": 0.5366023631237767, "recall": 0.0, "roc_auc": 0.5}`; std `{"balanced_accuracy": 0.0, "brier": 0.0026484735767384805, "f1": 0.0, "log_loss": 0.005314337656234964, "pr_auc": 0.015688518124700193, "precision": 0.0, "prevalence": 0.015688518124700193, "recall": 0.0, "roc_auc": 0.0}`; n=150,017 |
| `up_5s:logistic_fixed_c_1` | mean `{"balanced_accuracy": 0.49340038439182105, "brier": 0.2537114162460511, "f1": 0.16660682605560026, "log_loss": 0.7019731043652694, "pr_auc": 0.48000736374185937, "precision": 0.4981105576531708, "prevalence": 0.48097472087425697, "recall": 0.1387619877248051, "roc_auc": 0.48758272692775756}`; std `{"balanced_accuracy": 0.011306230065239804, "brier": 0.004057435162895523, "f1": 0.18145269249601387, "log_loss": 0.008619838136733013, "pr_auc": 0.015146891681813936, "precision": 0.010611859040466354, "prevalence": 0.023824823998770422, "recall": 0.1680553279961856, "roc_auc": 0.021557197346165416}`; n=150,304 |
| `up_5s:logistic_selected` | mean `{"balanced_accuracy": 0.4939589112051485, "brier": 0.25351898624753894, "f1": 0.1651684974195092, "log_loss": 0.7012565464317356, "pr_auc": 0.48025565638721607, "precision": 0.49696595128182847, "prevalence": 0.48097472087425697, "recall": 0.13705661305345782, "roc_auc": 0.4877058610839238}`; std `{"balanced_accuracy": 0.010298959792456241, "brier": 0.0038499622858889013, "f1": 0.1814176046256246, "log_loss": 0.008016767854550327, "pr_auc": 0.015663994431396065, "precision": 0.008833863546958223, "prevalence": 0.023824823998770422, "recall": 0.16672487325125632, "roc_auc": 0.020891936924293322}`; n=150,304 |
| `up_5s:majority_class_baseline` | mean `{"balanced_accuracy": 0.5, "brier": 0.48097472087329507, "f1": 0.0, "log_loss": 13.28982266870495, "pr_auc": 0.48097472087425697, "precision": 0.0, "prevalence": 0.48097472087425697, "recall": 0.0, "roc_auc": 0.5}`; std `{"balanced_accuracy": 0.0, "brier": 0.023824823998722752, "f1": 0.0, "log_loss": 0.6583042149932822, "pr_auc": 0.023824823998770422, "precision": 0.0, "prevalence": 0.023824823998770422, "recall": 0.0, "roc_auc": 0.0}`; n=150,304 |
| `up_5s:training_prevalence_baseline` | mean `{"balanced_accuracy": 0.5, "brier": 0.2504772247440561, "f1": 0.0, "log_loss": 0.6941118800581889, "pr_auc": 0.48097472087425697, "precision": 0.0, "prevalence": 0.48097472087425697, "recall": 0.0, "roc_auc": 0.5}`; std `{"balanced_accuracy": 0.0, "brier": 0.00237326715610815, "f1": 0.0, "log_loss": 0.004762734706848978, "pr_auc": 0.023824823998770422, "precision": 0.0, "prevalence": 0.023824823998770422, "recall": 0.0, "roc_auc": 0.0}`; n=150,304 |

## Date-block uncertainty

```json
{
  "fwd_open_to_close_ret_10s_adj:fold_2023:ridge_selected": {
    "dates": 246,
    "estimate": 0.0712026048994977,
    "lower_95": 0.0675299150973354,
    "replicates": 200,
    "upper_95": 0.07441010112844552
  },
  "fwd_open_to_close_ret_10s_adj:fold_2024:ridge_selected": {
    "dates": 246,
    "estimate": 0.08000657198648964,
    "lower_95": 0.07678249516926304,
    "replicates": 200,
    "upper_95": 0.0827866203519435
  },
  "fwd_open_to_close_ret_10s_adj:fold_2025:ridge_selected": {
    "dates": 250,
    "estimate": 0.07284475879098609,
    "lower_95": 0.07112063016400658,
    "replicates": 200,
    "upper_95": 0.07555784210006816
  },
  "fwd_open_to_close_ret_20s_adj:fold_2023:ridge_selected": {
    "dates": 246,
    "estimate": 0.10384752220051756,
    "lower_95": 0.09825362067089487,
    "replicates": 200,
    "upper_95": 0.10956915589251418
  },
  "fwd_open_to_close_ret_20s_adj:fold_2024:ridge_selected": {
    "dates": 246,
    "estimate": 0.11908415122431058,
    "lower_95": 0.11330722602684962,
    "replicates": 200,
    "upper_95": 0.12564452328839373
  },
  "fwd_open_to_close_ret_20s_adj:fold_2025:ridge_selected": {
    "dates": 250,
    "estimate": 0.10481426842426962,
    "lower_95": 0.10201811047021428,
    "replicates": 200,
    "upper_95": 0.10748846843847833
  },
  "fwd_open_to_close_ret_5s_adj:fold_2023:ridge_selected": {
    "dates": 246,
    "estimate": 0.05066294725381556,
    "lower_95": 0.04845173965157511,
    "replicates": 200,
    "upper_95": 0.05292681406120334
  },
  "fwd_open_to_close_ret_5s_adj:fold_2024:ridge_selected": {
    "dates": 246,
    "estimate": 0.05575545410540601,
    "lower_95": 0.05365321345898746,
    "replicates": 200,
    "upper_95": 0.05765849692348144
  },
  "fwd_open_to_close_ret_5s_adj:fold_2025:ridge_selected": {
    "dates": 250,
    "estimate": 0.05257256978775043,
    "lower_95": 0.051008514489283764,
    "replicates": 200,
    "upper_95": 0.054573286211198564
  },
  "up_10s:fold_2023:logistic_selected": {
    "dates": 246,
    "estimate": 0.7151787077190516,
    "lower_95": 0.7063921978199322,
    "replicates": 200,
    "upper_95": 0.7252023273716313
  },
  "up_10s:fold_2024:logistic_selected": {
    "dates": 246,
    "estimate": 0.7233401237874678,
    "lower_95": 0.7128261231673058,
    "replicates": 200,
    "upper_95": 0.7322652646024451
  },
  "up_10s:fold_2025:logistic_selected": {
    "dates": 250,
    "estimate": 0.6977070387414774,
    "lower_95": 0.6917560960170882,
    "replicates": 200,
    "upper_95": 0.7024498061413258
  },
  "up_20s:fold_2023:logistic_selected": {
    "dates": 246,
    "estimate": 0.7103395018248431,
    "lower_95": 0.7017116631103781,
    "replicates": 200,
    "upper_95": 0.7197958584951095
  },
  "up_20s:fold_2024:logistic_selected": {
    "dates": 246,
    "estimate": 0.745195362542561,
    "lower_95": 0.7322513125733793,
    "replicates": 200,
    "upper_95": 0.7572388410031778
  },
  "up_20s:fold_2025:logistic_selected": {
    "dates": 250,
    "estimate": 0.7021588089789105,
    "lower_95": 0.6983567118074926,
    "replicates": 200,
    "upper_95": 0.7057917012793324
  },
  "up_5s:fold_2023:logistic_selected": {
    "dates": 246,
    "estimate": 0.7070942742364865,
    "lower_95": 0.7000782795931852,
    "replicates": 200,
    "upper_95": 0.7145512487215243
  },
  "up_5s:fold_2024:logistic_selected": {
    "dates": 246,
    "estimate": 0.702259128303509,
    "lower_95": 0.6932281541528984,
    "replicates": 200,
    "upper_95": 0.7093732466452765
  },
  "up_5s:fold_2025:logistic_selected": {
    "dates": 250,
    "estimate": 0.6902357891714184,
    "lower_95": 0.6841386653231772,
    "replicates": 200,
    "upper_95": 0.6957330711504226
  }
}
```

Bootstrap resamples validation dates, never individual rows as the sole uncertainty unit. Fixed alpha/C=1 results remain alongside validation-selected variants. Negative R² values are retained. Classification probability metrics use probabilities, not threshold labels.

## Symbol-loss concentration

```json
{
  "fwd_open_to_close_ret_10s_adj": {
    "largest_loss_symbol": "PHDL",
    "largest_symbol_share": 0.3282705558177249,
    "symbols": 386,
    "top_10_symbol_share": 0.4127183761371213
  },
  "fwd_open_to_close_ret_20s_adj": {
    "largest_loss_symbol": "P01GIS150825",
    "largest_symbol_share": 0.42939844293105356,
    "symbols": 385,
    "top_10_symbol_share": 0.7059485957068751
  },
  "fwd_open_to_close_ret_5s_adj": {
    "largest_loss_symbol": "P01GIS150825",
    "largest_symbol_share": 0.17962631170002472,
    "symbols": 387,
    "top_10_symbol_share": 0.30832404787190326
  },
  "up_10s": {
    "largest_loss_symbol": "PHDL",
    "largest_symbol_share": 0.007196386361987302,
    "symbols": 386,
    "top_10_symbol_share": 0.05332189869194833
  },
  "up_20s": {
    "largest_loss_symbol": "PHDL",
    "largest_symbol_share": 0.006988472207233105,
    "symbols": 385,
    "top_10_symbol_share": 0.05357667388307939
  },
  "up_5s": {
    "largest_loss_symbol": "KAPCO",
    "largest_symbol_share": 0.005123377181783484,
    "symbols": 387,
    "top_10_symbol_share": 0.05092420727575368
  }
}
```

## Leakage controls

Median imputation and scaling are fitted separately on each task/fold training subset. Purged, embargoed, test, and not-in-fold rows are excluded. The final holdout is locked by default and was not scored. Feature columns exactly match the frozen C3 registry; identifiers and C4 target/future/split fields never enter matrices.
