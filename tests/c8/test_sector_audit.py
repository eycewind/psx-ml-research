from psx_ml.c8.relative_targets import build_relative_target_columns
from psx_ml.c8.sector_audit import sector_coverage_audit


def test_sector_audit_reason_precedence_and_counts():
    rows=[]
    for i,value in enumerate([1.,2.,3.,4.,5.,6.,None]): rows.append({"trade_date":"d","symbol":str(i),"sector":"large","fwd_open_to_close_ret_5s_adj":value})
    rows += [{"trade_date":"d","symbol":"S","sector":"small","fwd_open_to_close_ret_5s_adj":1.},{"trade_date":"d","symbol":"N","sector":None,"fwd_open_to_close_ret_5s_adj":1.}]
    relative=build_relative_target_columns(rows,(5,),5); detail,summary,coverage=sector_coverage_audit(rows,(5,),relative,5)
    reasons={r["symbol"]:r["invalid_reason"] for r in detail}
    assert reasons["6"]=="stock_target_missing" and reasons["S"]=="insufficient_sector_peers" and reasons["N"]=="missing_sector"
    assert reasons["0"]=="valid" and sum(r["row_count"] for r in summary)==len(rows)
    large=next(r for r in coverage if r["sector"]=="large")
    assert large["eligible_rows"]==7 and large["valid_sector_relative_rows"]==6


def test_peer_target_shortage_is_distinct_from_structural_shortage():
    rows=[{"trade_date":"d","symbol":str(i),"sector":"x","fwd_open_to_close_ret_5s_adj":1. if i<5 else None} for i in range(7)]
    relative=build_relative_target_columns(rows,(5,),5); detail,_,_=sector_coverage_audit(rows,(5,),relative,5)
    assert {r["invalid_reason"] for r in detail if r["symbol"] in {"0","1"}}=={"peer_targets_insufficient"}

def test_missing_sector_precedes_concurrent_stock_target_missing():
    rows=[{"trade_date":"d","symbol":"A","sector":None,"fwd_open_to_close_ret_5s_adj":None}]
    relative=build_relative_target_columns(rows,(5,),5); detail,_,_=sector_coverage_audit(rows,(5,),relative,5)
    assert detail[0]["invalid_reason"]=="missing_sector"
