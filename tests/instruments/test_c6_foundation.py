import pyarrow as pa
import pytest
from psx_ml.instruments.classify import classify_intervals, classify_observation, validate_intervals
from psx_ml.universe.variants import membership_rows
from psx_ml.diagnostics.robust_metrics import daily_ic, regression_robust

CFG={"manual_mappings":[{"symbol":"MAN","instrument_type":"REIT","confidence":"high"}],"sector_rules":{"36":"debt_security","0837":"ETF"},"ordinary_equity_sector_prefix":"08"}

def test_priority_unknown_and_heuristic_provenance():
    assert classify_observation("MAN","36",CFG)==("REIT","manual_mapping","high")
    assert classify_observation("ABCETF","0837",CFG)==("ETF","observed_sector_rule","low")
    assert classify_observation("ABC","",CFG)==("unknown","insufficient_metadata","unknown")

def test_intervals_order_invariant_and_nonoverlap():
    rows=[{"trade_date":"2024-01-01","symbol":"A","sector":"0801"},{"trade_date":"2024-01-02","symbol":"A","sector":"36"}]
    a=classify_intervals(pa.Table.from_pylist(rows),CFG); b=classify_intervals(pa.Table.from_pylist(rows[::-1]),CFG)
    assert a.to_pylist()==b.to_pylist(); validate_intervals(a)
    bad=pa.Table.from_pylist([{"symbol":"A","effective_from":"2024-01-01","effective_to":"2024-02-01","instrument_type":"ordinary_equity"},{"symbol":"A","effective_from":"2024-01-15","effective_to":"2024-03-01","instrument_type":"ordinary_equity"}])
    with pytest.raises(ValueError): validate_intervals(bad)

def test_membership_is_pit_and_target_prediction_independent():
    source=pa.Table.from_pylist([{"trade_date":"2024-01-01","symbol":"A"},{"trade_date":"2024-01-02","symbol":"A"}])
    pit=pa.Table.from_pylist([{"trade_date":"2024-01-01","symbol":"A","eligible":False},{"trade_date":"2024-01-02","symbol":"A","eligible":True}])
    classes=pa.Table.from_pylist([{"symbol":"A","effective_from":"2024-01-01","effective_to":"2024-01-02","instrument_type":"ordinary_equity"}])
    out=membership_rows(source,pit,classes,{"equity":{"instrument_types":["ordinary_equity"]}}).to_pylist()
    assert [x["eligible"] for x in out]==[False,True] and out[0]["exclusion_reason"]=="liquidity_exclusion"

def test_robust_metrics_hand_values_and_daily_minimum():
    m=regression_robust([0,1,10],[0,2,0],trim_fraction=1/3,huber_delta=1)
    assert m["median_absolute_error"]==1 and m["rmse"]==pytest.approx((101/3)**.5) and m["trimmed_rmse"]==pytest.approx((1/2)**.5)
    assert daily_ic(["d"]*3,[1,2,3],[1,2,3],minimum=4)["dates"]==0
    assert daily_ic(["d"]*3,[1,2,3],[1,2,3],minimum=3)["mean_daily_ic"]==pytest.approx(1)
