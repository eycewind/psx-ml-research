import pandas as pd
from psx_ml.c11.deployment_decision import (
    PRIMARY_CANDIDATE,
    SECONDARY_CANDIDATE,
    build_finalist_scorecard,
    select_primary_deployment,
)


def test_finalist_scorecard_join() -> None:
    allocation = pd.DataFrame(
        {
            "allocation_id": [PRIMARY_CANDIDATE, SECONDARY_CANDIDATE],
            "starting_capital": [1_000_000.0, 1_000_000.0],
            "annualized_return": [0.53, 0.45],
            "sharpe_zero_rf": [1.66, 1.68],
            "max_drawdown": [-0.21, -0.18],
        }
    )
    concentration = pd.DataFrame(
        {
            "allocation_id": [PRIMARY_CANDIDATE, SECONDARY_CANDIDATE],
            "starting_capital": [1_000_000.0, 1_000_000.0],
            "realized_max_name_worst": [0.38, 0.65],
            "realized_max_sector_worst": [0.46, 0.65],
        }
    )
    out = build_finalist_scorecard(allocation, concentration)
    assert len(out) == 2
    assert set(out["allocation_id"]) == {
        PRIMARY_CANDIDATE,
        SECONDARY_CANDIDATE,
    }


def test_primary_selection_is_policy_frozen_not_metric_argmax() -> None:
    scorecard = pd.DataFrame(
        {
            "allocation_id": [PRIMARY_CANDIDATE, SECONDARY_CANDIDATE],
            "annualized_return": [0.40, 0.60],
            "sharpe_zero_rf": [1.50, 2.00],
            "max_drawdown": [-0.20, -0.10],
            "realized_max_name_worst": [0.35, 0.65],
            "realized_max_sector_worst": [0.40, 0.65],
        }
    )
    # Even when A17 is made superior on return/Sharpe in this fixture, the
    # function is not an argmax optimizer. It preserves the frozen policy
    # choice provided the documented concentration rationale still holds.
    assert select_primary_deployment(scorecard) == PRIMARY_CANDIDATE
