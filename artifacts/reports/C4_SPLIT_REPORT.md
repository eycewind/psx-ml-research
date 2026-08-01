# C4 Temporal Split Report

Split set `expanding_annual_v1` v1. All symbols on a feature date share a role; no random row split exists.

Final untouched holdout: 2026-01-01 through 2026-07-10. Primary purge horizon: 20 sessions. Embargo: 5 exchange sessions.

## Fold evidence

### fold_2023

Train begins 2020-01-01; validation 2023-01-01 through 2023-12-31.

Counts: `{"embargo_dates": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"], "embargoed": 1844, "maximum_training_target_end_date": "2022-12-30", "not_in_fold": 218966, "overlap_violations": 0, "purged": 6846, "test": 63469, "train": 248575, "validation": 82094}`

### fold_2024

Train begins 2020-01-01; validation 2024-01-01 through 2024-12-31.

Counts: `{"embargo_dates": ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-06", "2025-01-07"], "embargoed": 2297, "maximum_training_target_end_date": "2023-12-29", "not_in_fold": 116479, "overlap_violations": 0, "purged": 7981, "test": 63469, "train": 329534, "validation": 102034}`

### fold_2025

Train begins 2020-01-01; validation 2025-01-01 through 2025-12-31.

Counts: `{"embargo_dates": [], "embargoed": 0, "maximum_training_target_end_date": "2024-12-31", "not_in_fold": 0, "overlap_violations": 0, "purged": 9922, "test": 63469, "train": 429627, "validation": 118776}`

Every included training row satisfies `target_end_date_20s < validation_start`; overlap violations are zero. Rows at the boundary that violate this condition are explicitly `purged`. Configured post-validation session dates are `embargoed` unless they belong to the higher-priority untouched final test window.
