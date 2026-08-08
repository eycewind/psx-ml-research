from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from psx_ml.c11.shariah_gate import normalize_screening_history


EXPECTED_BRANCH = "feature/c11-deployment-policy"
ACCEPTED_C10_TAG = "c10-fee-aware-portfolio-accepted"
ACCEPTED_C10_COMMIT = "612db3c"
FINAL_HOLDOUT_START = pd.Timestamp("2026-01-01")

C9_SELECTIONS = Path("data/processed/c9/candidate_selections.parquet")
P4_SELECTIONS = Path("data/processed/c10/p4_kmi30_selections.parquet")
P5_SELECTIONS = Path("data/processed/c10/p5_shariah_screened_selections.parquet")
SHARIAH_HISTORY = Path("data/reference/kmi_all_share_screened_universe_history.csv")

EXPECTED_HASHES = {
    C9_SELECTIONS: "3ff902152a75d168218850535d4c40da4dd949b54e22ccdfc6560d39646dc520",
    P4_SELECTIONS: "75ef50328110d573649906d47ee08733b60977953bb7c67c37d869eae05fd03c",
    P5_SELECTIONS: "0166c4a67c6d12241ddef1b7f7fc4002d6fa8071d01cbd6499b32dd22811c57c",
    SHARIAH_HISTORY: "525bb1e26e4b9ec71b838122b27e63ce1c95755f4b244991973f6d2da949f70a",
}

REPORT_PATH = Path("artifacts/reports/C11_CP1_DEPLOYMENT_FREEZE_REPORT.md")
MANIFEST_PATH = Path("artifacts/reports/C11_CP1_INPUT_MANIFEST.json")

P5_PROVENANCE_COLUMNS = {
    "membership_confidence",
    "membership_source",
    "screening_snapshot_date",
    "screening_effective_from",
    "screening_effective_to",
}


@dataclass(frozen=True)
class ArtifactAudit:
    path: str
    sha256: str
    rows: int
    min_signal_date: str | None
    max_signal_date: str | None
    policy_ids: list[str]
    holdout_rows: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "rows": self.rows,
            "min_signal_date": self.min_signal_date,
            "max_signal_date": self.max_signal_date,
            "policy_ids": self.policy_ids,
            "holdout_rows": self.holdout_rows,
        }


def _git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def sha256_file(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Required C11 input is missing: {path}")
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_git_baseline() -> dict[str, str]:
    branch = _git("branch", "--show-current")
    if branch != EXPECTED_BRANCH:
        raise ValueError(
            f"C11 CP1 must run on {EXPECTED_BRANCH}; current branch is {branch!r}"
        )

    head = _git("rev-parse", "HEAD")
    tag_commit = _git("rev-list", "-n", "1", ACCEPTED_C10_TAG)
    accepted_full = _git("rev-parse", ACCEPTED_C10_COMMIT)
    if tag_commit != accepted_full:
        raise ValueError(
            f"Accepted C10 tag does not resolve to {ACCEPTED_C10_COMMIT}: {tag_commit}"
        )

    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", accepted_full, "HEAD"],
        check=False,
    )
    if ancestor.returncode != 0:
        raise ValueError("Current C11 branch does not descend from accepted C10")

    return {
        "branch": branch,
        "head": head,
        "accepted_c10_tag": ACCEPTED_C10_TAG,
        "accepted_c10_commit": accepted_full,
    }


def _read_artifact(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported CP1 artifact format: {path}")


def audit_selection_artifact(
    path: Path,
    *,
    expected_policy_ids: set[str],
) -> ArtifactAudit:
    actual_hash = sha256_file(path)
    expected_hash = EXPECTED_HASHES[path]
    if actual_hash != expected_hash:
        raise ValueError(
            f"Frozen artifact hash mismatch for {path}: "
            f"expected {expected_hash}, found {actual_hash}"
        )

    frame = _read_artifact(path)
    required = {"trade_date", "policy_id", "symbol"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{path} missing required columns: {missing}")

    dates = pd.to_datetime(frame["trade_date"], errors="raise").dt.normalize()
    holdout_rows = int((dates >= FINAL_HOLDOUT_START).sum())
    if holdout_rows:
        raise ValueError(f"Holdout access denied in {path}: {holdout_rows} rows")

    policies = sorted(frame["policy_id"].dropna().astype(str).unique().tolist())
    missing_policies = sorted(expected_policy_ids - set(policies))
    if missing_policies:
        raise ValueError(f"{path} missing expected policies: {missing_policies}")

    return ArtifactAudit(
        path=str(path),
        sha256=actual_hash,
        rows=len(frame),
        min_signal_date=dates.min().date().isoformat() if len(frame) else None,
        max_signal_date=dates.max().date().isoformat() if len(frame) else None,
        policy_ids=policies,
        holdout_rows=holdout_rows,
    )


def audit_shariah_history(path: Path = SHARIAH_HISTORY) -> dict[str, Any]:
    actual_hash = sha256_file(path)
    expected_hash = EXPECTED_HASHES[path]
    if actual_hash != expected_hash:
        raise ValueError(
            f"Frozen artifact hash mismatch for {path}: "
            f"expected {expected_hash}, found {actual_hash}"
        )

    frame = normalize_screening_history(_read_artifact(path))
    if (frame["effective_from"] >= FINAL_HOLDOUT_START).any():
        raise ValueError("2026 Shariah history rows encountered during CP1")

    return {
        "path": str(path),
        "sha256": actual_hash,
        "rows": len(frame),
        "min_effective_from": frame["effective_from"].min().date().isoformat(),
        "max_effective_from": frame["effective_from"].max().date().isoformat(),
        "confidence_values": sorted(frame["membership_confidence"].unique().tolist()),
        "eligible_rows": int(frame["is_shariah_screened_eligible"].sum()),
    }


def verify_p5_provenance(path: Path = P5_SELECTIONS) -> dict[str, Any]:
    frame = pd.read_parquet(path)
    missing = sorted(P5_PROVENANCE_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"P5 selections missing Shariah provenance columns: {missing}")

    required_non_null = P5_PROVENANCE_COLUMNS - {"screening_effective_to"}
    null_columns = sorted(
        col for col in required_non_null if frame[col].isna().any()
    )
    if null_columns:
        raise ValueError(f"P5 provenance contains null values: {null_columns}")

    confidence = sorted(frame["membership_confidence"].astype(str).unique().tolist())
    return {
        "required_columns": sorted(P5_PROVENANCE_COLUMNS),
        "confidence_values": confidence,
        "membership_sources": sorted(
            frame["membership_source"].astype(str).unique().tolist()
        ),
    }


def build_manifest() -> dict[str, Any]:
    git_info = verify_git_baseline()

    # Snapshot hashes before reading anything. CP1 is read-only with respect to
    # all accepted upstream artifacts; after-audit hashes must remain identical.
    before_hashes = {str(path): sha256_file(path) for path in EXPECTED_HASHES}

    c9 = audit_selection_artifact(
        C9_SELECTIONS,
        expected_policy_ids={"P1_broad_canonical", "P2_conservative_consensus"},
    )
    p4 = audit_selection_artifact(
        P4_SELECTIONS,
        expected_policy_ids={"P4_kmi30_strict"},
    )
    p5 = audit_selection_artifact(
        P5_SELECTIONS,
        expected_policy_ids={"P5_shariah_screened"},
    )
    history = audit_shariah_history()
    provenance = verify_p5_provenance()

    after_hashes = {str(path): sha256_file(path) for path in EXPECTED_HASHES}
    if before_hashes != after_hashes:
        raise ValueError("Accepted upstream artifacts changed during C11 CP1")

    return {
        "checkpoint": "C11-CP1",
        "contract": "C11",
        "status": "COMPLETE",
        "holdout_accessed": False,
        "git": git_info,
        "frozen_policies": [
            "P1_broad_canonical",
            "P2_conservative_consensus",
            "P4_kmi30_strict",
            "P5_shariah_screened",
        ],
        "deployment_policy": {
            "shariah_gate_version": "C11-CP1-v1",
            "universal_buy_gate": True,
            "unknown_eligibility_action": "reject",
            "ineligible_action": "reject",
            "low_confidence_action": "allow_but_flag",
            "sector_inference_allowed": False,
            "p1_p2_original_policy_mutation_allowed": False,
            "p1_p2_deployment_variants_to_evaluate": [
                "filter_only",
                "filter_and_refill",
            ],
        },
        "cp2_capital_grid_pkr": [50000, 100000, 250000, 500000, 1000000],
        "inputs": {
            str(C9_SELECTIONS): c9.to_dict(),
            str(P4_SELECTIONS): p4.to_dict(),
            str(P5_SELECTIONS): p5.to_dict(),
            str(SHARIAH_HISTORY): history,
        },
        "p5_provenance": provenance,
        "immutability": {
            "before": before_hashes,
            "after": after_hashes,
            "unchanged": True,
        },
    }


def render_report(manifest: dict[str, Any]) -> str:
    inputs = manifest["inputs"]
    lines = [
        "# C11 CP1 — Deployment Freeze Report",
        "",
        f"- Branch: `{manifest['git']['branch']}`",
        f"- HEAD: `{manifest['git']['head']}`",
        f"- Accepted C10 tag: `{manifest['git']['accepted_c10_tag']}`",
        f"- Holdout accessed: `{str(manifest['holdout_accessed']).lower()}`",
        "",
        "## Frozen upstream policies",
        "",
    ]
    for policy in manifest["frozen_policies"]:
        lines.append(f"- `{policy}`")

    lines += [
        "",
        "## Mandatory deployment Shariah gate",
        "",
        "- Every executable BUY candidate must pass PIT Shariah eligibility.",
        "- Ineligible candidates are rejected.",
        "- Unknown/unavailable eligibility is rejected.",
        "- Low-confidence eligible candidates are allowed but explicitly flagged.",
        "- Sector names are not used as a proxy for Shariah eligibility.",
        "- P1/P2 remain immutable research policies; C11 will derive gated deployment variants.",
        "",
        "## Frozen inputs",
        "",
        "| Artifact | Rows | Date range | Policies / confidence | SHA-256 |",
        "|---|---:|---|---|---|",
    ]

    for path, item in inputs.items():
        if "policy_ids" in item:
            date_range = f"{item['min_signal_date']} to {item['max_signal_date']}"
            detail = ", ".join(item["policy_ids"])
        else:
            date_range = f"{item['min_effective_from']} to {item['max_effective_from']}"
            detail = "confidence=" + ",".join(item["confidence_values"])
        lines.append(
            f"| `{path}` | {item['rows']} | {date_range} | {detail} | `{item['sha256']}` |"
        )

    lines += [
        "",
        "## CP2 capital grid",
        "",
        "PKR 50,000; 100,000; 250,000; 500,000; 1,000,000.",
        "",
        "## Boundaries",
        "",
        "- No model retraining or signal redesign.",
        "- No C8/C9/C10 accepted artifact mutation.",
        "- No 2026 holdout use for policy design or tuning.",
        "- C11 deployment transformations must remain traceable to their upstream policy.",
        "",
        "## Result",
        "",
        "CP1 input freeze and deployment-gate specification: **PASS**.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    manifest = build_manifest()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    report = render_report(manifest)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"Report:   {REPORT_PATH}")


if __name__ == "__main__":
    main()
