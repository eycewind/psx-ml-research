import pandas as pd
import pytest
from psx_ml.c11.concentration_overlap import pairwise_selection_overlap, target_concentration_by_date

def test_target_concentration_basic() -> None:
    targets = pd.DataFrame({
        "policy_id": ["A", "A", "A"],
        "trade_date": pd.to_datetime(["2025-01-01"] * 3),
        "symbol": ["AAA", "BBB", "CCC"],
        "target_weight": [0.5, 0.3, 0.2],
    })
    sectors = pd.DataFrame({
        "trade_date": pd.to_datetime(["2025-01-01"] * 3),
        "symbol": ["AAA", "BBB", "CCC"],
        "sector": ["X", "X", "Y"],
    })
    out = target_concentration_by_date(targets, sectors).iloc[0]
    assert out["max_name_weight"] == pytest.approx(0.5)
    assert out["top3_name_weight"] == pytest.approx(1.0)
    assert out["name_hhi"] == pytest.approx(0.38)
    assert out["effective_name_count"] == pytest.approx(1 / 0.38)
    assert out["max_sector_weight"] == pytest.approx(0.8)

def test_pairwise_overlap_jaccard() -> None:
    df = pd.DataFrame({
        "policy_id": ["P1", "P1", "P2", "P2"],
        "trade_date": pd.to_datetime(["2025-01-01"] * 4),
        "symbol": ["AAA", "BBB", "BBB", "CCC"],
    })
    out = pairwise_selection_overlap(df, ["P1", "P2"]).iloc[0]
    assert out["intersection_count"] == 1
    assert out["union_count"] == 3
    assert out["jaccard"] == pytest.approx(1 / 3)
    assert out["overlap_left_fraction"] == pytest.approx(0.5)
    assert out["overlap_right_fraction"] == pytest.approx(0.5)


def test_realized_sector_mapping_handles_asof_history() -> None:
    from psx_ml.c11.concentration_overlap import realized_concentration_by_date

    positions = pd.DataFrame(
        {
            "allocation_id": ["A", "A"],
            "starting_capital": [1_000_000.0, 1_000_000.0],
            "trade_date": pd.to_datetime(["2025-01-10", "2025-02-10"]),
            "symbol": ["AAA", "AAA"],
            "weight_close": [1.0, 1.0],
        }
    )
    sectors = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(["2025-01-01", "2025-02-01"]),
            "symbol": ["AAA", "AAA"],
            "sector": ["OLD", "NEW"],
        }
    )
    out = realized_concentration_by_date(positions, sectors)
    assert len(out) == 2
    assert (out["unknown_sector_weight_of_invested"] == 0.0).all()
