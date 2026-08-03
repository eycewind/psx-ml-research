from psx_ml.c10.policies import (
    P1_BROAD_CANONICAL,
    P2_CONSERVATIVE_CONSENSUS,
)


def test_p1_is_frozen() -> None:
    assert P1_BROAD_CANONICAL.to_dict() == {
        "policy_id": "P1_broad_canonical",
        "models": ["lightgbm_cpu"],
        "target": "fwd_market_relative_rank_5s",
        "feature_variant": "B_market_context",
        "selection": "top_10pct",
        "rebalance": "weekly_first_session",
        "sector_cap": 2,
        "liquidity_screen": "L0",
    }


def test_p2_is_frozen() -> None:
    assert P2_CONSERVATIVE_CONSENSUS.to_dict() == {
        "policy_id": "P2_conservative_consensus",
        "models": ["lightgbm_cpu", "xgboost_gpu"],
        "target": "fwd_market_relative_rank_5s",
        "feature_variant": "B_market_context",
        "selection": "intersection_top_10pct",
        "rebalance": "weekly_first_session",
        "sector_cap": 2,
        "liquidity_screen": "L1",
    }
