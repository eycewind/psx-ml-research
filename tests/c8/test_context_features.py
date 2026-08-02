from psx_ml.c8.context_features import build_context_features

def _rows(dates=35):
    return [{"trade_date":f"2024-01-{d:02d}","symbol":s,"sector":"x","ret_1obs_adj":v+d/1000,"ret_5obs_adj":v*5,"ret_20obs_adj":v*20,"turnover_1obs_adj":100+v,"turnover_median_20obs_adj":90+v,"close_to_mean_20obs_adj":v} for d in range(1,dates+1) for s,v in zip("ABCDEF",[-.03,-.02,-.01,.01,.02,.03])]

def test_context_features_are_leave_one_out_and_have_history_minimum():
    rows=_rows(); f=build_context_features(rows,minimum_sector_peers=5,minimum_rolling=30)
    assert f["market_median_ret_1obs"][0]>.0
    assert f["market_mean_ret_1obs"][0]>.0
    assert f["sector_eligible_symbol_count"][0]==5
    assert f["rolling_beta_market_60obs"][0] is None
    assert f["rolling_beta_market_60obs"][-1] is not None

def test_future_append_does_not_change_earlier_context():
    rows=_rows(10); before=build_context_features(rows,5,60,5)
    future=[{**r,"trade_date":"2025-01-01"} for r in _rows(1)]
    after=build_context_features(rows+future,5,60,5)
    for name,values in before.items(): assert after[name][:len(rows)]==values
