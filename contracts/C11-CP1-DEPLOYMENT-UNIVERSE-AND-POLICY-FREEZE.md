# C11 — Deployment Policy, Capital Allocation & Live Order Construction

## CP1 — Deployment Universe & Policy Freeze

**Status:** DRAFT  
**Branch:** `feature/c11-deployment-policy`  
**Parent baseline:** `main` at accepted C10 tag `c10-fee-aware-portfolio-accepted`  
**Accepted C10 merge commit:** `612db3c`

---

## 1. Purpose

C11 converts the already accepted C10 research policies into deployable trading decisions.

CP1 freezes the policy inputs, research boundaries, Shariah deployment gate, artifact provenance, and holdout rules before any capital-allocation or live-order logic is implemented.

CP1 does **not** create a new alpha model, retrain any model, alter C8/C9 rankings, or optimize policy weights.

---

## 2. Accepted upstream policies

C11 shall consume the following accepted C10 policies without modifying their historical definitions:

| Policy | Accepted C10 meaning | C11 role |
|---|---|---|
| `P1_broad_canonical` | Broad canonical LightGBM policy | Research benchmark; may be Shariah-gated for deployment diagnostics |
| `P2_conservative_consensus` | Conservative consensus policy | Primary risk-adjusted candidate; must be Shariah-gated before deployment |
| `P4_kmi30_strict` | Strict point-in-time KMI-30 policy | Shariah-compliant deployment candidate |
| `P5_shariah_screened` | Point-in-time PSX Shariah-screened policy | Shariah-compliant deployment candidate |

The C10 definitions of P1, P2, P4 and P5 are immutable within C11.

Any C11 transformation must create a new deployment-stage representation rather than rewriting the accepted C10 policy outputs.

---

## 3. C10 source-artifact freeze

CP1 shall build a machine-readable C11 input manifest containing at minimum:

- repository commit and accepted C10 tag;
- path, row count and SHA-256 for each C10 artifact consumed by C11;
- policy IDs present in each applicable artifact;
- minimum and maximum signal dates;
- explicit confirmation that no 2026 holdout rows were consumed during CP1.

At minimum, CP1 shall verify and freeze these selection artifacts:

- `data/processed/c9/candidate_selections.parquet`
- `data/processed/c10/p4_kmi30_selections.parquet`
- `data/processed/c10/p5_shariah_screened_selections.parquet`

Known accepted hashes from C10 are:

| Artifact | Accepted SHA-256 |
|---|---|
| `data/processed/c9/candidate_selections.parquet` | `3ff902152a75d168218850535d4c40da4dd949b54e22ccdfc6560d39646dc520` |
| `data/processed/c10/p4_kmi30_selections.parquet` | `75ef50328110d573649906d47ee08733b60977953bb7c67c37d869eae05fd03c` |
| `data/processed/c10/p5_shariah_screened_selections.parquet` | `0166c4a67c6d12241ddef1b7f7fc4002d6fa8071d01cbd6499b32dd22811c57c` |

CP1 shall fail closed if any frozen artifact does not match its accepted hash.

Additional C10 artifacts may be frozen later in CP1 if required for C11 evaluation, but their hashes must be discovered from the accepted repository state and recorded rather than guessed.

---

## 4. No retraining / no signal redesign

C11 CP1 freezes the following research boundary:

- no model retraining;
- no model hyperparameter search;
- no new ML target;
- no new feature set;
- no new technical indicator added for alpha generation;
- no modification of C8 prediction values;
- no modification of C9 ranking logic;
- no modification of C10 policy definitions;
- no optimization using the locked 2026 holdout.

C11 may transform accepted signals only for **deployment mechanics**, including:

- Shariah eligibility filtering;
- whole-share sizing;
- capital-aware sizing;
- liquidity/capacity constraints;
- order-price rules;
- execution skips;
- policy combination;
- duplicate/overlap handling;
- residual cash handling.

---

## 5. Mandatory Shariah deployment gate

### 5.1 Core rule

No C11-generated **executable BUY order** may contain a security that fails or lacks point-in-time Shariah eligibility, regardless of which upstream policy generated the candidate.

This is a hard deployment requirement.

The rule applies to:

- P1-derived deployment candidates;
- P2-derived deployment candidates;
- P4-derived deployment candidates;
- P5-derived deployment candidates;
- any combined or consensus portfolio;
- any final production order artifact.

### 5.2 Eligibility decision

For a candidate with signal date `D`, C11 shall resolve Shariah eligibility using only information effective on or before `D`.

The result shall be one of:

| Eligibility state | Deployment action |
|---|---|
| `eligible = true` | Candidate may proceed |
| `eligible = false` | Reject |
| eligibility unavailable / unknown | Reject |

The gate must be **point-in-time**. Future screening information may not be used to determine historical eligibility.

### 5.3 Source of truth

C11 shall reuse the point-in-time Shariah-screening history accepted in C10 rather than infer compliance from sector names.

Therefore, C11 must **not** apply blanket rules such as:

- reject all banks;
- reject all insurance companies;
- accept all non-financial companies.

A compliant Islamic bank, takaful company, or other Shariah-compliant financial security may remain eligible if the accepted point-in-time screening source marks it eligible.

### 5.4 P4 and P5

P4 and P5 already incorporate Shariah-compliant universes upstream.

C11 must still carry the eligibility metadata forward and may verify the gate defensively, but it must not silently assume eligibility without provenance.

### 5.5 P1 and P2

P1 and P2 remain unchanged as accepted research policies.

For deployment, C11 shall derive Shariah-gated variants rather than modifying the original policy outputs.

CP4 shall explicitly evaluate at least:

1. **Filter-only**
   - remove non-compliant/unknown candidates;
   - do not replace rejected names;
   - allow fewer holdings.

2. **Filter-and-refill**
   - remove non-compliant/unknown candidates;
   - continue down the original accepted ranking;
   - refill only with the next eligible names;
   - preserve the intended portfolio size where possible.

The choice between these variants must be made by an explicit C11 acceptance decision and not by ad-hoc live behavior.

---

## 6. Shariah source confidence

Every Shariah-gated deployment candidate shall preserve, where available:

- `shariah_eligible`
- `shariah_source`
- `shariah_confidence`
- screening snapshot/effective date
- signal date used for the PIT decision

Initial C11 handling:

- `medium` / `high` confidence: eligible candidate may proceed;
- `low` confidence: eligible candidate may proceed but must be flagged;
- unknown eligibility: reject.

Low-confidence eligibility is therefore **not automatically rejected** in CP1.

Any later decision to forbid low-confidence names must be explicit, tested, and versioned. It must not be introduced silently during live-order generation.

---

## 7. 2026 holdout boundary

The 2026 holdout remains locked during C11 policy design and parameter selection.

For CP1 through CP6:

- no 2026 historical outcome data may be used for tuning;
- no 2026 returns may be used to choose policy weights;
- no 2026 performance may be used to choose filter-only vs refill;
- no 2026 outcome data may be used to select execution thresholds.

When C11 reaches production/live operation, current 2026 market information may be consumed to create forward-looking orders **only after the deployment policy has been frozen**.

Live/current data must not be used retrospectively to tune C11 and then claim an untouched holdout result.

Any deliberate one-time opening of the 2026 holdout for final evaluation requires a separate explicit checkpoint and acceptance decision.

---

## 8. C11 deployment candidates

CP1 defines the following candidate families for later checkpoints:

### Research/reference

- `P1_broad_canonical`
- `P2_conservative_consensus`
- `P4_kmi30_strict`
- `P5_shariah_screened`

### Deployable derivatives

Names are provisional but should remain explicit and traceable, for example:

- `D_P1_shariah_filter`
- `D_P1_shariah_refill`
- `D_P2_shariah_filter`
- `D_P2_shariah_refill`
- `D_P4_kmi30_strict`
- `D_P5_shariah_screened`

No deployable derivative may overwrite its upstream C10 artifact.

---

## 9. Capital assumptions frozen for CP2

CP2 shall evaluate at least the following nominal capital levels:

- PKR 50,000
- PKR 100,000
- PKR 250,000
- PKR 500,000
- PKR 1,000,000

The purpose is to quantify how accepted policies behave under realistic whole-share deployment.

CP1 does not yet choose a preferred capital level.

---

## 10. Repository and output boundaries

C11 work shall be performed only on:

`feature/c11-deployment-policy`

It shall be merged to `main` only after C11 acceptance.

C11 may write only within the `psx-ml-research` repository.

Generated C11 artifacts shall use dedicated locations such as:

- `data/processed/c11/`
- `artifacts/reports/C11_*`

C11 shall not modify:

- `psx_watcher.db`;
- C8 accepted model artifacts;
- C9 accepted ranking artifacts;
- C10 accepted output artifacts.

---

## 11. Required CP1 implementation outputs

CP1 implementation shall produce at minimum:

1. `artifacts/reports/C11_CP1_INPUT_MANIFEST.json`
2. `artifacts/reports/C11_CP1_DEPLOYMENT_FREEZE_REPORT.md`

The manifest shall include:

- current Git commit;
- required accepted C10 tag;
- input artifact hashes;
- row counts;
- signal-date ranges;
- policy IDs;
- holdout-access status;
- Shariah gate policy version/definition.

The report shall summarize:

- upstream policies;
- frozen deployment constraints;
- Shariah eligibility rules;
- holdout rules;
- accepted CP2 capital grid;
- any missing or inconsistent source artifact.

---

## 12. CP1 fail-closed conditions

CP1 must fail if any of the following occurs:

- repository is not based on the accepted C10 state;
- required C10 tag cannot be verified;
- required artifact is missing;
- required artifact hash differs from accepted value;
- expected policy ID is missing;
- unexpected 2026 rows are encountered;
- P5 Shariah provenance columns required by C11 are absent;
- a PIT Shariah mapping cannot be uniquely resolved where it is expected;
- C11 attempts to write into accepted C8/C9/C10 artifacts.

---

## 13. Acceptance tests

CP1 is accepted only when all of the following pass.

### AT-1 — Git baseline

Verify:

- current branch is `feature/c11-deployment-policy`;
- accepted C10 tag `c10-fee-aware-portfolio-accepted` exists;
- C11 branch ancestry includes accepted C10 merge commit `612db3c`.

**PASS:** all three conditions true.

### AT-2 — Frozen selection artifacts

Verify the accepted hashes for:

- C9 candidate selections;
- P4 selections;
- P5 selections.

**PASS:** all hashes match exactly.

### AT-3 — Policy presence

Verify:

- P1 and P2 exist in C9 candidate selections;
- P4 exists in P4 selections;
- P5 exists in P5 selections.

**PASS:** all required policy IDs present.

### AT-4 — Holdout lock

Check all CP1-consumed historical selection artifacts.

**PASS:** maximum signal date is before `2026-01-01`, and manifest records `holdout_accessed = false`.

### AT-5 — P5 Shariah provenance

Verify P5 selections contain at minimum:

- `membership_confidence`;
- `membership_source`;
- `screening_snapshot_date`;
- `screening_effective_from`;
- `screening_effective_to`.

**PASS:** all required columns exist and are populated according to the accepted C10 P5 design.

### AT-6 — Universal deployment gate specification

Unit-test the gate independently of policy origin:

- eligible P1 candidate -> pass;
- ineligible P1 candidate -> reject;
- eligible P2 candidate -> pass;
- ineligible P2 candidate -> reject;
- eligible P4 candidate -> pass;
- eligible P5 candidate -> pass;
- unknown candidate -> reject.

**PASS:** no executable candidate bypasses the gate because of policy origin.

### AT-7 — No blanket sector rule

Create test fixtures containing:

- conventional financial security marked non-compliant;
- Shariah-compliant financial security marked compliant.

**PASS:** decision follows PIT Shariah eligibility, not sector label.

### AT-8 — Low-confidence behavior

Test an eligible candidate with `membership_confidence = low`.

**PASS:** candidate remains eligible but is explicitly flagged as low-confidence.

### AT-9 — Unknown behavior

Test candidate with no PIT eligibility record.

**PASS:** rejected.

### AT-10 — Artifact immutability

Record hashes of all accepted C9/C10 input artifacts before and after CP1.

**PASS:** hashes are unchanged.

### AT-11 — Manifest reproducibility

Run the CP1 manifest builder twice from an unchanged repository/data state.

**PASS:** source hashes, row counts, date ranges and policy metadata are identical.

### AT-12 — C11 test suite

Run:

```bash
python -m pytest -q tests/c11
```

**PASS:** all C11 CP1 tests pass.

---

## 14. CP1 completion criteria

CP1 is complete when:

- all acceptance tests pass;
- required report and manifest are generated;
- Git working tree contains only expected C11 changes;
- no C10 artifact has changed;
- CP1 is committed on `feature/c11-deployment-policy`;
- the branch is pushed;
- CP1 has been explicitly reviewed and accepted before CP2 begins.

Suggested commit message:

```text
C11 CP1: freeze deployment policies and Shariah gate
```

---

## 15. CP1 non-goals

CP1 deliberately does not decide:

- which policy will be used live;
- P2 filter-only vs refill;
- final P2/P4/P5 capital allocation;
- position-size formula;
- maximum number of simultaneous holdings;
- live limit-price formula;
- stop-loss logic;
- opening-gap threshold;
- order expiry;
- partial-fill behavior;
- final production order schema.

Those decisions belong to later C11 checkpoints after the deployment boundary and Shariah gate are frozen.
