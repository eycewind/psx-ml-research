from __future__ import annotations

import pandas as pd
import pytest

from psx_ml.c11.shariah_gate import (
    decide_shariah_eligibility,
    normalize_screening_history,
)


def _history() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": ["P1OK", "P1NO", "P2OK", "P2NO", "P4OK", "P5OK", "ISLBANK"],
            "effective_from": ["2025-01-01"] * 7,
            "effective_to": [None] * 7,
            "screening_snapshot_date": ["2024-12-31"] * 7,
            "membership_source": ["fixture"] * 7,
            "membership_confidence": [
                "medium", "medium", "low", "medium", "high", "medium", "medium"
            ],
            "is_shariah_screened_eligible": [True, False, True, False, True, True, True],
            "sector": [
                "TEXTILE", "BANK", "CEMENT", "INSURANCE", "ENERGY", "TECH", "BANK"
            ],
        }
    )


@pytest.mark.parametrize(
    ("policy_id", "symbol", "expected"),
    [
        ("P1_broad_canonical", "P1OK", True),
        ("P1_broad_canonical", "P1NO", False),
        ("P2_conservative_consensus", "P2OK", True),
        ("P2_conservative_consensus", "P2NO", False),
        ("P4_kmi30_strict", "P4OK", True),
        ("P5_shariah_screened", "P5OK", True),
    ],
)
def test_gate_is_independent_of_policy_origin(
    policy_id: str,
    symbol: str,
    expected: bool,
) -> None:
    # policy_id is intentionally not passed to the gate: eligibility cannot be
    # bypassed merely because a candidate came from P4/P5 or any other policy.
    assert policy_id
    decision = decide_shariah_eligibility(
        _history(), symbol=symbol, signal_date="2025-03-03"
    )
    assert decision.shariah_eligible is expected


def test_unknown_candidate_is_rejected() -> None:
    decision = decide_shariah_eligibility(
        _history(), symbol="UNKNOWN", signal_date="2025-03-03"
    )
    assert decision.shariah_eligible is False
    assert decision.gate_status == "rejected_unknown"


def test_low_confidence_candidate_is_allowed_but_flagged() -> None:
    decision = decide_shariah_eligibility(
        _history(), symbol="P2OK", signal_date="2025-03-03"
    )
    assert decision.shariah_eligible is True
    assert decision.shariah_confidence == "low"
    assert decision.low_confidence_flag is True
    assert decision.gate_status == "eligible_flagged_low_confidence"


def test_sector_is_not_used_as_compliance_proxy() -> None:
    decision = decide_shariah_eligibility(
        _history(), symbol="ISLBANK", signal_date="2025-03-03"
    )
    assert decision.shariah_eligible is True
    assert decision.shariah_source == "fixture"


def test_point_in_time_interval_boundary() -> None:
    history = pd.DataFrame(
        {
            "symbol": ["AAA", "AAA"],
            "effective_from": ["2025-01-01", "2025-06-01"],
            "effective_to": ["2025-06-01", None],
            "screening_snapshot_date": ["2024-12-31", "2025-05-31"],
            "membership_source": ["first", "second"],
            "membership_confidence": ["medium", "medium"],
            "is_shariah_screened_eligible": [True, False],
        }
    )
    before = decide_shariah_eligibility(
        history, symbol="AAA", signal_date="2025-05-30"
    )
    after = decide_shariah_eligibility(
        history, symbol="AAA", signal_date="2025-06-01"
    )
    assert before.shariah_eligible is True
    assert after.shariah_eligible is False


def test_overlapping_intervals_fail_closed() -> None:
    history = pd.DataFrame(
        {
            "symbol": ["AAA", "AAA"],
            "effective_from": ["2025-01-01", "2025-05-01"],
            "effective_to": ["2025-06-01", None],
            "screening_snapshot_date": ["2024-12-31", "2025-04-30"],
            "membership_source": ["first", "second"],
            "membership_confidence": ["medium", "medium"],
            "is_shariah_screened_eligible": [True, False],
        }
    )
    with pytest.raises(ValueError, match="Overlapping"):
        normalize_screening_history(history)
