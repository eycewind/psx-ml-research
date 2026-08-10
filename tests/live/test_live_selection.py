import pandas as pd
from psx_ml.c11.live_orders import P4, P5
from psx_ml.live.live_selection import build_live_selections


def test_live_selection_reuses_p4_p5_mechanics() -> None:
    day = pd.Timestamp("2026-08-10")
    predictions = pd.DataFrame({
        "trade_date": [day] * 6,
        "symbol": ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"],
        "fold_id": ["fold_2025"] * 6,
        "horizon": [5] * 6,
        "target_family": ["market_relative_rank"] * 6,
        "feature_variant": ["B_market_context"] * 6,
        "model_name": ["lightgbm_cpu"] * 6,
        "prediction": [0.60, 0.59, 0.58, 0.57, 0.56, 0.55],
        "sector": ["A", "B", "C", "D", "E", "F"],
    })
    features = pd.DataFrame({
        "trade_date": [day] * 6,
        "symbol": ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"],
        "turnover_median_20obs_adj": [100, 90, 80, 70, 60, 50],
    })
    kmi30 = pd.DataFrame({
        "symbol": ["AAA", "BBB", "CCC"],
        "effective_from": ["2025-11-24"] * 3,
        "effective_to": ["9999-12-31"] * 3,
    })
    screened = pd.DataFrame({
        "symbol": ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"],
        "effective_from": [pd.Timestamp("2025-12-02")] * 6,
        "effective_to": [pd.NaT] * 6,
        "screening_snapshot_date": [pd.Timestamp("2025-12-02")] * 6,
        "membership_source": ["official_full_screening_table"] * 6,
        "membership_confidence": ["medium"] * 6,
        "is_shariah_screened_eligible": [True] * 6,
    })
    out = build_live_selections(predictions=predictions, features=features, kmi30_history=kmi30, screened_history=screened, date=day)
    assert set(out["policy_id"]) == {P4, P5}
    assert out["shariah_eligible"].all()
    assert out["shariah_source"].notna().all()
    assert out["shariah_confidence"].notna().all()
