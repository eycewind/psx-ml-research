# C4 Target Report

Target set `next_session_open_to_future_close` v1; 621,794 rows, 821 symbols, 2020-01-01 through 2026-07-10.

## Timing and warning

Features through close D enter only at adjusted open on the exact next exchange session. Exits use adjusted close exactly H sessions after entry. Targets are gross returns without costs and must not be described as profitable trades.

## Coverage, null reasons, percentiles, and class balance

- `fwd_open_to_close_ret_1s_adj`: {"null": 77545, "null_reasons": {"insufficient_future_sessions": 1008, "missing_entry_open": 3031, "missing_exit_observation": 26466, "missing_next_session_observation": 47040}, "valid": 544249}
- `fwd_open_to_close_ret_5s_adj`: {"null": 85338, "null_reasons": {"insufficient_future_sessions": 3005, "missing_entry_open": 3031, "missing_exit_observation": 32262, "missing_next_session_observation": 47040}, "valid": 536456}
- `fwd_open_to_close_ret_10s_adj`: {"null": 90480, "null_reasons": {"insufficient_future_sessions": 5460, "missing_entry_open": 3031, "missing_exit_observation": 34949, "missing_next_session_observation": 47040}, "valid": 531314}
- `fwd_open_to_close_ret_20s_adj`: {"null": 98340, "null_reasons": {"insufficient_future_sessions": 10432, "missing_entry_open": 3031, "missing_exit_observation": 37837, "missing_next_session_observation": 47040}, "valid": 523454}
- `up_5s`: {"negative_or_zero": 285578, "positive": 250878, "valid": 536456}
- `up_10s`: {"negative_or_zero": 275365, "positive": 255949, "valid": 531314}
- `up_20s`: {"negative_or_zero": 262573, "positive": 260881, "valid": 523454}
- `fwd_ret_5s_rank`: {"population_max": 314, "population_median": 181.0, "population_min": 0, "valid": 301577}
- `fwd_ret_20s_rank`: {"population_max": 314, "population_median": 180.0, "population_min": 0, "valid": 296601}

Return percentiles:

- `fwd_open_to_close_ret_1s_adj`: {"p01": -0.1333333333333333, "p05": -0.07734223573499233, "p25": -0.02533783783783794, "p50": -0.002491103202846956, "p75": 0.02036363636363636, "p95": 0.09090909090909083, "p99": 0.17054248388957213}
- `fwd_open_to_close_ret_5s_adj`: {"p01": -0.20231525554299964, "p05": -0.11553398058252431, "p25": -0.039548022598870136, "p50": -0.0027700831024930483, "p75": 0.03720593389311516, "p95": 0.15822784810126578, "p99": 0.35669303530018776}
- `fwd_open_to_close_ret_10s_adj`: {"p01": -0.25150102311610545, "p05": -0.14545456810972623, "p25": -0.05077543702919671, "p50": -0.00186886782293344, "p75": 0.05360443622920519, "p95": 0.22007039999567424, "p99": 0.5050439393939391}
- `fwd_open_to_close_ret_20s_adj`: {"p01": -0.3096338241856314, "p05": -0.18992588517436845, "p25": -0.06722252459099123, "p50": 0.0, "p75": 0.08333333333333326, "p95": 0.32130738491551547, "p99": 0.7485512901253142}

## PIT rank populations

Ranks use only same-feature-date eligible rows with valid targets, deterministic average ties, and minimum population 20.

## Hand-reconciled examples

| Symbol | Feature D | Entry | Entry price | End | Exit price | Stored return | Recalculated |
|---|---|---|---:|---|---:|---:|---:|
| 786 | 2020-01-01 | 2020-01-02 | 25.21 | 2020-01-30 | 29.41 | 0.16660056 | 0.16660056 |
| AABS | 2020-01-01 | 2020-01-02 | 260 | 2020-01-30 | 224 | -0.13846154 | -0.13846154 |
| ABL | 2020-01-01 | 2020-01-02 | 98 | 2020-01-30 | 94.88 | -0.03183673 | -0.03183673 |

Missing symbol observations are not forward-filled; missing/nonpositive prices and insufficient calendar horizons remain null with explicit reasons. Open/close outside high-low does not invalidate an otherwise valid target. No infinities remain.
