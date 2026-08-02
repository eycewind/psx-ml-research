from psx_ml.c8.benchmarks import date_local_rank,leave_one_out_median
from psx_ml.c8.relative_targets import build_relative_target_columns


def test_leave_one_out_market_matches_hand_calculation():
    got=leave_one_out_median(["d"]*4,[1.,2.,4.,8.],list("ABCD"))
    assert got==[4.,4.,2.,2.]


def test_sector_minimum_is_after_exclusion_and_missing_stays_null():
    dates=["d"]*5; values=[1.,2.,3.,4.,5.]; symbols=list("ABCDE")
    assert leave_one_out_median(dates,values,symbols,["x"]*5,minimum_peers=5)==[None]*5
    got=leave_one_out_median(dates+["d"],values+[9.],symbols+["F"],["x"]*5+[None],minimum_peers=4)
    assert got[:5]==[3.5,3.5,3.,2.5,2.5] and got[5] is None


def test_date_local_rank_boundaries_and_ties_are_deterministic():
    a=date_local_rank(["d"]*4,[2.,1.,2.,4.],list("BACD"))
    b=date_local_rank(["d"]*4,[2.,1.,2.,4.],list("BACD"))
    assert a==b and min(a)==0 and max(a)==1 and a[0]<a[2]


def test_relative_targets_and_single_member_sector():
    rows=[{"trade_date":"d","symbol":s,"sector":sector,"fwd_open_to_close_ret_5s_adj":v} for s,sector,v in [("A","x",.1),("B","x",.2),("C","y",-.1)]]
    out=build_relative_target_columns(rows,horizons=(5,),minimum_sector_peers=1)
    assert out["fwd_market_relative_ret_5s"]==[.05,.2,-.25]
    assert out["fwd_sector_relative_ret_5s"]==[-.1,.1,None]
    assert out["outperform_market_5s"]==[1,1,0]


def test_future_date_append_does_not_change_earlier_targets():
    base=[{"trade_date":"d1","symbol":s,"sector":"x","fwd_open_to_close_ret_5s_adj":v} for s,v in zip("ABC",[1.,2.,3.])]
    future={"trade_date":"d2","symbol":"A","sector":"x","fwd_open_to_close_ret_5s_adj":100.}
    before=build_relative_target_columns(base,horizons=(5,),minimum_sector_peers=1)
    after=build_relative_target_columns(base+[future],horizons=(5,),minimum_sector_peers=1)
    assert all(after[k][:3]==v for k,v in before.items())
