# C4 Delivery and Acceptance Report

## Summary

C4 produces exact-session, gross forward targets and deterministic purged
walk-forward assignments from accepted C1/C3 research artifacts only. It runs
CPU-only, makes no SQLite connections, and contains no model, prediction,
signal, portfolio, cost, execution, or backtest logic.

Branch: `feature/c4-targets-and-temporal-splits`. Contract commit: `349886f`.
Implementation commit: `d079e4c`. Live report commit: `18df67c`.

## Target timing and live coverage

After-close feature date D enters at adjusted open on the exact next global PSX
session. H-session exits use adjusted close exactly H exchange sessions after
entry. A missing symbol row never causes a jump to a later observation.

| Horizon | Valid | Null |
|---:|---:|---:|
| 1 | 544,249 | 77,545 |
| 5 | 536,456 | 85,338 |
| 10 | 531,314 | 90,480 |
| 20 | 523,454 | 98,340 |

Nulls reconcile to missing exact-session entry/exit observations, missing entry
opens, and insufficient future sessions. No nonpositive-price cases occurred in
the live snapshot, but synthetic canaries cover them. Gross classifications
derive exactly from regression targets. PIT rank validity is 301,577 rows at
five sessions and 296,601 at twenty sessions.

These are gross labels without transaction costs and are not profitability
claims.

## Split design and safety

Three expanding folds validate on 2023, 2024, and 2025. The final untouched
holdout is 2026-01-01 through 2026-07-10 (63,469 rows per fold). The five-session
post-validation embargo applies where it does not overlap the higher-priority
holdout. Primary purge horizon is 20 sessions.

| Fold | Train | Validation | Purged | Embargoed | Test | Maximum train target end | Overlap violations |
|---|---:|---:|---:|---:|---:|---|---:|
| fold_2023 | 248,575 | 82,094 | 6,846 | 1,844 | 63,469 | 2022-12-30 | 0 |
| fold_2024 | 329,534 | 102,034 | 7,981 | 2,297 | 63,469 | 2023-12-29 | 0 |
| fold_2025 | 429,627 | 118,776 | 9,922 | 0 | 63,469 | 2024-12-31 | 0 |

Every symbol on a feature date shares the same role within a fold. Every included
training target ends strictly before validation starts.

## Deterministic live outputs

Two clean executions produced identical file and logical hashes:

```text
labelled rows: 621794
split rows:    1865382
target file:   8ef1d78a54cd2d0492e6e75fb3b9961708dde8b9a75fd31076aa5768c8590f69
target logical:680a178e9ae9ae3507c4f8cd9be810eb3b268a0a6fe8b30fb3a38f0e5ac2cea3
split file:    aebbc1dd688e3a462c7a069559c162f28c595dd2041f2d4e0c5e361c07959d58
split logical: 33a11caf7f7df60959dc74f7768943165715b56dee64252ec955b595b719559a
```

Final CPU-only repository suite:

```text
41 passed, 1 expected C2 GPU skip in 8.38s
```

## Acceptance mapping

| Contract checks | Evidence |
|---|---|
| 1–5 boundaries | Research Parquet/JSON/TOML only; SQLite canary; `tmp_path`; watcher/outside paths rejected |
| 6–12 target alignment/nulls | Exact global calendar synthetic examples, hand returns, missing entry/exit, nonpositive entry, insufficient horizon canaries |
| 13–15 invariance/PSX | Future append and other-symbol invariance; outside high/low columns do not invalidate targets |
| 16–20 labels/ranks/infinity | Classification reconciliation, exact-date eligible ranks, average ties, ineligible nulls, no retained infinity |
| 21–23 date-level chronological split | Date-uniform roles, deterministic config-only logic, no random APIs |
| 24–27 purge/embargo/holdout | Actual `target_end_date_20s` purge, explicit reasons, exact embargo dates, test priority and isolation |
| 28–30 stability/counts | Input-order and post-final-boundary invariance; per-fold counts in tracked manifest |
| 31–36 determinism/provenance | Two matching file/logical hash pairs, registry/schema equality, manifest reconciliation, config-hash canaries, Git state recorded |
| 37 full suite | Complete C1–C4 suite run with CUDA hidden; one C2 GPU test skips |
| 38–40 scope/watcher | No prohibited research/evaluation logic; gross warning; C14 untouched |

## Source safety

Before implementation and after all live generation:

```text
DB SHA-256: e35f224284481ab00650d6f65e495f79318f7580f340ebd6bf23fd3f08aeb67b
DB size: 304885760
DB mtime: 1785003631
Watcher HEAD: 404e3637637ca89d4455b9f7069c6191a3658d83
Watcher porcelain status: <empty>
```

## Deviations and judgments

- TOML is used instead of suggested YAML, matching C1/C3 configuration and
  avoiding another parser dependency.
- The full labelled panel is canonical; the optional eligible-only panel is not
  generated because later contracts can filter the retained eligibility column.
- Exit H means H exchange sessions after entry, exactly as the contract states;
  the 1-session label therefore exits on the session after entry, not entry-day
  close.
- Target-end calendar dates are recorded even when a symbol lacks the exit row.
  This permits date-uniform, actual-end-date purging without hiding null targets.
- Test is higher priority than embargo when the final holdout begins immediately
  after a validation period, preserving the untouched holdout definition.
- Runtime manifests remain beside ignored binary outputs; the small accepted
  manifest is copied to `artifacts/reports/C4_TARGET_SPLIT_MANIFEST.json`.
- The supplied Windows `Zone.Identifier` sidecar is ignored as filesystem
  metadata and was not committed or interpreted as contract content.

## Recommendation

C4 is recommended for review and acceptance. Do not merge before review. C4
does not establish predictive value or profitability.
