from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from psx_ml.c11.checkpoint1 import (
    FINAL_HOLDOUT_START,
    P5_PROVENANCE_COLUMNS,
    audit_selection_artifact,
    render_report,
)


def test_holdout_boundary_constant() -> None:
    assert FINAL_HOLDOUT_START == pd.Timestamp("2026-01-01")


def test_p5_provenance_contract_is_frozen() -> None:
    assert P5_PROVENANCE_COLUMNS == {
        "membership_confidence",
        "membership_source",
        "screening_snapshot_date",
        "screening_effective_from",
        "screening_effective_to",
    }


def test_missing_artifact_fails_closed(tmp_path: Path) -> None:
    missing = tmp_path / "missing.parquet"
    with pytest.raises(FileNotFoundError, match="missing"):
        audit_selection_artifact(
            missing,
            expected_policy_ids={"P1_broad_canonical"},
        )


def test_report_states_mandatory_gate() -> None:
    manifest = {
        "git": {
            "branch": "feature/c11-deployment-policy",
            "head": "abc",
            "accepted_c10_tag": "c10-fee-aware-portfolio-accepted",
        },
        "holdout_accessed": False,
        "frozen_policies": ["P1_broad_canonical"],
        "inputs": {},
    }
    report = render_report(manifest)
    assert "Every executable BUY candidate must pass PIT Shariah eligibility" in report
    assert "Unknown/unavailable eligibility is rejected" in report
    assert "Low-confidence eligible candidates are allowed but explicitly flagged" in report
