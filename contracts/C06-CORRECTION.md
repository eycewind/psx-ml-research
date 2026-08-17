# C6 Classification Audit and Rule-Traceability Correction

Continue work in:

```text
/home/hassan/psx-ml-research
```

Required branch:

```text
feature/c6-universe-refinement-and-robust-evaluation
```

Do not modify:

```text
/home/hassan/psx-stock-watcher
/home/hassan/psx-stock-watcher/data/psx_watcher.db
```

Do not interact with or modify the pending watcher C14 branch.

## Context

C6 currently generates:

```text
data/processed/universe/c6_instrument_classification.parquet
data/processed/universe/c6_universe_membership.parquet
artifacts/reports/C6_INSTRUMENT_REPORT.md
artifacts/reports/C6_UNIVERSE_REPORT.md
artifacts/reports/C6_MANIFEST.json
```

The current classification schema is:

```text
symbol
effective_from
effective_to
instrument_type
classification_source
classification_confidence
observed_sector
```

The current classifier hierarchy is approximately:

1. manual mapping;
2. government-security ticker heuristic;
3. exact observed-sector rule;
4. ETF ticker heuristic;
5. debt ticker heuristic;
6. right/entitlement ticker heuristic;
7. sector prefix `08`:

   * preference suffix → `preference_share`;
   * otherwise → `ordinary_equity`;
8. otherwise → `unknown`.

Current results report zero unknown intervals because all remaining observations appear to have sectors beginning with `08`.

The current implementation is reproducible, but the classification output does not record the exact rule that produced each decision, and the assumption that every relevant `08` sector belongs to an ordinary equity has not been audited sufficiently.

## Required work

### 1. Inspect the live configuration and classification code

Inspect:

```text
config/instruments.yaml
src/psx_ml/instruments/classify.py
src/psx_ml/instruments/pipeline.py
src/psx_ml/instruments/taxonomy.py
tests/instruments/
```

Document the actual rule hierarchy and all configured exact sector mappings.

Do not assume meanings beyond what the repository data supports.

### 2. Add explicit classification rule traceability

Add a required output field:

```text
classification_rule
```

It must record the exact rule that produced the classification.

Suggested values include:

```text
manual_mapping:<symbol>
ticker_regex:government_security
sector_exact:<sector_code>
ticker_suffix:ETF
ticker_regex:debt_security
ticker_regex:right_or_entitlement
sector_prefix:08+preference_suffix
sector_prefix:08
no_rule_matched
```

Use clear deterministic values that reflect the actual implementation.

Update:

* classification return structure;
* Parquet schema;
* manifests;
* reports;
* tests.

### 3. Audit classification-source and confidence counts

Produce deterministic counts by:

```text
instrument_type
classification_source
classification_confidence
classification_rule
observed_sector
```

The instrument report must clearly state how many ordinary-equity intervals are inferred through the `08` sector-prefix rule versus exact sector mappings or manual review.

Do not describe low-confidence inferred ordinary-equity classifications as authoritative.

### 4. Audit all distinct observed sector codes

Generate a deterministic sector audit table containing:

```text
observed_sector
assigned instrument_type
classification_source
classification_rule
interval_count
unique_symbol_count
example_symbols
```

Save the runtime table under a research-owned ignored path, for example:

```text
data/processed/diagnostics/c6_sector_classification_audit.parquet
```

Summarize it in:

```text
artifacts/reports/C6_INSTRUMENT_REPORT.md
```

### 5. Detect competing-rule and hierarchy conflicts

For every classification observation, evaluate which rules could potentially match before applying precedence.

Generate diagnostics for cases where more than one rule matches, including examples such as:

* government-like ticker plus equity-sector prefix;
* debt-like ticker plus equity sector;
* ETF suffix plus another exact sector;
* right/entitlement ticker plus ordinary-equity sector;
* preference suffix plus exact sector mapping.

Create a deterministic conflict table such as:

```text
symbol
observed_sector
winning_rule
winning_type
competing_rules
effective_from
effective_to
```

Save it under:

```text
data/processed/diagnostics/c6_classification_rule_conflicts.parquet
```

Do not automatically change precedence unless evidence supports doing so. Report the conflicts first.

### 6. Create a targeted manual-review queue

Do not request manual review of all symbols.

Build a compact deterministic review queue containing only high-value cases:

1. top C5 squared-loss contributors for the 5-, 10-, and 20-session Ridge tasks;
2. all rule-conflict symbols;
3. all symbols with multiple classification intervals;
4. government/debt/security-like symbols that entered the PIT liquid universe;
5. unusual ordinary-equity classifications produced only by `sector_prefix:08`;
6. symbols with extreme C4 target returns;
7. symbols with very short listing intervals or maturity-like ticker patterns.

Include, where available:

```text
symbol
effective_from
effective_to
instrument_type
classification_source
classification_confidence
classification_rule
observed_sector
PIT eligible row count
C5 loss contribution
extreme-target count
review_priority
review_reason
```

Write:

```text
artifacts/reports/C6_MANUAL_REVIEW_QUEUE.csv
```

This small review queue may remain tracked if appropriate.

### 7. Handle ordinary-equity confidence honestly

Do not automatically convert all `sector_prefix:08` rows to `unknown`.

Instead:

* retain current classification unless evidence shows the rule is wrong;
* ensure `classification_confidence` remains low for prefix-inferred rows;
* make the report explicitly state that these are inferred ordinary equities;
* distinguish exact sector mappings from generic `08` prefix inference;
* preserve explicit unknown behavior for observations without matching evidence.

If repository documentation contains an authoritative sector-code definition, cite or record it in provenance. If it does not, state the limitation clearly.

### 8. Reconcile zero unknown intervals

Explain precisely why the current snapshot has zero unknown intervals.

The report should state whether:

* every interval had a configured exact rule;
* or every unmatched interval had a sector beginning with `08`;
* or another reason applies.

Do not imply that zero unknowns means authoritative classification.

### 9. Add or update tests

Acceptance tests must cover at least:

1. every output row has `classification_rule`;
2. manual mappings record the exact manual rule;
3. exact sector mappings record the exact sector code;
4. generic `08` inference is distinguishable from exact sector mappings;
5. unmatched observations remain `unknown`;
6. rule conflict diagnostics are deterministic;
7. precedence is tested explicitly;
8. review-queue membership is deterministic;
9. residual magnitude does not change universe membership;
10. target value does not change universe membership;
11. future rows cannot change earlier classification intervals;
12. output row ordering does not affect logical hashes;
13. original C1 PIT eligibility remains unchanged;
14. no SQLite connections occur;
15. source database and watcher repository remain unchanged;
16. complete C1–C6 CPU-only suite passes with CUDA hidden.

### 10. Continue C6 robust diagnostics only after this audit

Once classification traceability and the review queue are complete, continue the remaining C6 work:

* outlier and loss-concentration diagnostics;
* robust regression metrics;
* universe-variant comparisons;
* same-date ranking diagnostics;
* fold/year/liquidity/instrument-type stratification;
* recommendation or rejection of an ordinary-equity universe for C7.

Do not introduce tree models, boosting, neural networks, brokerage fees, signals, portfolio logic, execution simulation, or backtesting.

## Required reports and delivery

Update or produce:

```text
artifacts/reports/C6_INSTRUMENT_REPORT.md
artifacts/reports/C6_UNIVERSE_REPORT.md
artifacts/reports/C6_ROBUST_EVALUATION_REPORT.md
contracts/C06-DELIVERY.md
artifacts/reports/C6_MANIFEST.json
artifacts/reports/C6_MANUAL_REVIEW_QUEUE.csv
```

The delivery report must explain:

* what was changed;
* why zero unknown intervals occurred;
* how many classifications use exact mappings versus generic prefix inference;
* what conflicts were detected;
* which symbols require manual review;
* whether the C5 negative linear conclusion changes;
* whether a refined universe is recommended for C7;
* test results;
* determinism hashes;
* production-source fingerprints.

## Git and safety requirements

Before implementation:

```bash
git branch --show-current
git status --short
```

Required branch:

```text
feature/c6-universe-refinement-and-robust-evaluation
```

Do not merge the branch.

Commit the completed correction and reports on the C6 branch and push them for review.

Do not access the locked final 2026 holdout.

## Acceptance principle

The objective is not to classify every security manually. The objective is to make the classifier explainable, quantify uncertainty, detect rule conflicts, and produce a small high-priority manual-review queue.

Do not remove instruments merely because they worsen model performance.
