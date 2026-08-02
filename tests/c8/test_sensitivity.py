import pytest
from psx_ml.c8.relative_targets import build_relative_target_columns
from psx_ml.c8.sensitivity import sensitivity_audit

def test_fixed_shrinkage_rule_and_tiers():
    rows=[{"trade_date":"d","symbol":str(i),"sector":"x","fwd_open_to_close_ret_5s_adj":v} for i,v in enumerate([0.,1.,2.,3.])]
    out=build_relative_target_columns(rows,(5,),5,3,5.)
    assert out["sector_valid_peer_count_5s"]==[3]*4
    assert out["sector_benchmark_weight_5s"]==[.375]*4
    assert out["sector_benchmark_tier_5s"]==["relaxed_3_peer"]*4
    expected=.375*2.+.625*2.
    assert out["sector_market_shrunk_benchmark_ret_5s"][0]==pytest.approx(expected)
    assert out["fwd_sector_relative_ret_5s"][0] is None

def test_sensitivity_has_natural_and_matched_subsets():
    rows=[{"trade_date":"d","symbol":str(i),"sector":"x","fwd_open_to_close_ret_5s_adj":float(i)} for i in range(6)]
    out=build_relative_target_columns(rows,(5,),5,3,5.); summary,coverage=sensitivity_audit(rows,(5,),out)
    assert len(summary)==6 and {r["comparison_subset"] for r in summary}=={"natural_coverage","strict_5_peer_matched"}
    assert len(coverage)==3
