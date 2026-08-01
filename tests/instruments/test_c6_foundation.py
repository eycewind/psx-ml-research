import pyarrow as pa
import pytest
from psx_ml.instruments.classify import classify_intervals, classify_observation, validate_intervals
from psx_ml.instruments.audit import rule_conflicts, sector_audit
from psx_ml.instruments.review import build_review_queue
from psx_ml.universe.variants import membership_rows
from psx_ml.diagnostics.robust_metrics import daily_ic, regression_robust

CFG={"manual_mappings":[{"symbol":"MAN","instrument_type":"REIT","confidence":"high"}],"sector_rules":{"36":"debt_security","0837":"ETF"},"ordinary_equity_sector_prefix":"08"}

def test_priority_unknown_and_heuristic_provenance():
    assert classify_observation("MAN","36",CFG)==("REIT","manual_mapping","high","manual_mapping:MAN")
    assert classify_observation("ABCETF","0837",CFG)==("ETF","observed_sector_rule","low","sector_exact:0837")
    assert classify_observation("ABC","",CFG)==("unknown","insufficient_metadata","unknown","no_rule_matched")

def test_intervals_order_invariant_and_nonoverlap():
    rows=[{"trade_date":"2024-01-01","symbol":"A","sector":"0801"},{"trade_date":"2024-01-02","symbol":"A","sector":"36"}]
    a=classify_intervals(pa.Table.from_pylist(rows),CFG); b=classify_intervals(pa.Table.from_pylist(rows[::-1]),CFG)
    assert a.to_pylist()==b.to_pylist(); validate_intervals(a); assert all(r["classification_rule"] for r in a.to_pylist())
    bad=pa.Table.from_pylist([{"symbol":"A","effective_from":"2024-01-01","effective_to":"2024-02-01","instrument_type":"ordinary_equity"},{"symbol":"A","effective_from":"2024-01-15","effective_to":"2024-03-01","instrument_type":"ordinary_equity"}])
    with pytest.raises(ValueError): validate_intervals(bad)

def test_exact_prefix_distinction_conflicts_and_precedence():
    source=pa.Table.from_pylist([{"trade_date":"2024-01-01","symbol":"ABCETF","sector":"0837"},{"trade_date":"2024-01-01","symbol":"XR","sector":"0801"}])
    intervals=classify_intervals(source,CFG)
    rules={r["symbol"]:r["classification_rule"] for r in intervals.to_pylist()}
    assert rules=={"ABCETF":"sector_exact:0837","XR":"ticker_regex:right_or_entitlement"}
    conflicts=rule_conflicts(source,CFG).to_pylist(); assert [r["symbol"] for r in conflicts]==["ABCETF","XR"]
    assert "ticker_suffix:ETF" in conflicts[0]["competing_rules"] and "sector_prefix:08" in conflicts[1]["competing_rules"]
    assert sector_audit(intervals).num_rows==2

def test_membership_is_pit_and_target_prediction_independent():
    source=pa.Table.from_pylist([{"trade_date":"2024-01-01","symbol":"A"},{"trade_date":"2024-01-02","symbol":"A"}])
    pit=pa.Table.from_pylist([{"trade_date":"2024-01-01","symbol":"A","eligible":False},{"trade_date":"2024-01-02","symbol":"A","eligible":True}])
    classes=pa.Table.from_pylist([{"symbol":"A","effective_from":"2024-01-01","effective_to":"2024-01-02","instrument_type":"ordinary_equity"}])
    out=membership_rows(source,pit,classes,{"equity":{"instrument_types":["ordinary_equity"]}}).to_pylist()
    assert [x["eligible"] for x in out]==[False,True] and out[0]["exclusion_reason"]=="liquidity_exclusion"
    changed=source.append_column("target",pa.array([999.0,-999.0])).append_column("residual",pa.array([1e9,-1e9]))
    assert membership_rows(changed,pit,classes,{"equity":{"instrument_types":["ordinary_equity"]}}).to_pylist()==out

def test_robust_metrics_hand_values_and_daily_minimum():
    m=regression_robust([0,1,10],[0,2,0],trim_fraction=1/3,huber_delta=1)
    assert m["median_absolute_error"]==1 and m["rmse"]==pytest.approx((101/3)**.5) and m["trimmed_rmse"]==pytest.approx((1/2)**.5)
    assert daily_ic(["d"]*3,[1,2,3],[1,2,3],minimum=4)["dates"]==0
    assert daily_ic(["d"]*3,[1,2,3],[1,2,3],minimum=3)["mean_daily_ic"]==pytest.approx(1)

def test_future_observation_does_not_change_earlier_classification_and_review_is_deterministic():
    old=[{"trade_date":"2024-01-01","symbol":"A","sector":"0801"}]
    future=old+[{"trade_date":"2025-01-01","symbol":"A","sector":"36"}]
    assert classify_intervals(pa.Table.from_pylist(old),CFG).to_pylist()[0]["classification_rule"]==classify_intervals(pa.Table.from_pylist(future),CFG).to_pylist()[0]["classification_rule"]
    intervals=classify_intervals(pa.Table.from_pylist(old),CFG); conflicts=rule_conflicts(pa.Table.from_pylist(old),CFG)
    pit=pa.Table.from_pylist([{"symbol":"A","eligible":True}]); pred=pa.Table.from_pylist([{"symbol":"A","target_name":"y","target":2.0,"prediction":0.0,"model_name":"ridge_fixed_alpha_1"}])
    targets=pa.Table.from_pylist([{"symbol":"A","fwd_open_to_close_ret_5s_adj":1.0,"fwd_open_to_close_ret_10s_adj":0.0,"fwd_open_to_close_ret_20s_adj":0.0}])
    one=build_review_queue(intervals,conflicts,pit,pred,targets,{"5":.5,"10":.75,"20":1.0})
    two=build_review_queue(intervals,conflicts,pit,pred,targets,{"5":.5,"10":.75,"20":1.0})
    assert one==two and one[0]["symbol"]=="A" and "top_c5_squared_loss" in one[0]["review_reason"]
