# C9 Baseline Report

Random selection preserves same-date candidate counts. Momentum and liquidity use point-in-time ranks.

| baseline | policy_id | mean_outcome | mean_spread | precision | outcome_ci_lower | outcome_ci_upper | repetitions | distribution_std | empirical_p_value |
|---|---|---|---|---|---|---|---|---|---|
| random_same_count | P1_broad_canonical | 0.008132090503509833 | None | None | 0.005655312816989704 | 0.01092961023180671 | 1000 | 0.0013184263805043615 | 0.001998001998001998 |
| relative_momentum | P1_broad_canonical | 0.006173529976428216 | -0.0021812576601682866 | 0.17474579170439258 | 0.0013751428181505534 | 0.010959397622291145 | None | None | None |
| liquidity_rank | P1_broad_canonical | 0.006615583838464763 | -0.0016713623940074714 | 0.1096907606535695 | 0.00365184978794166 | 0.009863842633954149 | None | None | None |
| c7_absolute_return_model | P1_broad_canonical | 0.008532683914560326 | 0.0004084739213778086 | 0.11502336668213764 | 0.004021659338070355 | 0.013988331705238966 | None | None | None |
| c8_market_relative_regression | P1_broad_canonical | 0.008168800542326108 | 2.013977642044568e-06 | 0.12281557964366256 | 0.0033145162830304827 | 0.013265948181381151 | None | None | None |
