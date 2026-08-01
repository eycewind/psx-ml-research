import numpy as np

from psx_ml.targets.forward_returns import generate_targets
from tests.targets.conftest import DATES,daily_row,tables,tconfig

def keyed(table): return {(r["trade_date"],r["symbol"]):r for r in table.to_pylist()}

def test_exact_next_session_entry_and_exchange_horizon(target_rows,tmp_path):
    out,metrics,calendar=generate_targets(*tables(target_rows),tconfig(tmp_path)); r=keyed(out)[(DATES[0],"A")]
    assert r["entry_date"]==DATES[1]
    assert r["target_end_date_1s"]==DATES[2]
    assert np.isclose(r["fwd_open_to_close_ret_1s_adj"],103/101-1) # entry open day2, exit close day3
    assert r["target_end_date_5s"]==DATES[6]
    assert np.isclose(r["fwd_open_to_close_ret_5s_adj"],107/101-1)

def test_missing_exact_entry_and_invalid_open_reasons(target_rows,tmp_path):
    out,_,_=generate_targets(*tables(target_rows),tconfig(tmp_path)); rows=keyed(out)
    assert rows[(DATES[0],"C")]["target_null_reason_1s"]=="missing_next_session_observation"
    assert rows[(DATES[2],"C")]["target_null_reason_1s"]=="missing_exit_observation" # entry day4 valid; exact exit day5 absent
    # Feature day1 C cannot jump to day3, even though it has a row there.
    assert rows[(DATES[0],"C")]["entry_date"]==DATES[1]


def test_nonpositive_entry_open_has_explicit_reason(tmp_path):
    rows=[]
    for i,d in enumerate(DATES[:4]): rows.append(daily_row(d,"A",0 if i==1 else 10,11,True))
    out,_,_=generate_targets(*tables(rows),tconfig(tmp_path)); r=keyed(out)[(DATES[0],"A")]
    assert r["target_null_reason_1s"]=="nonpositive_entry_open"
    assert r["fwd_open_to_close_ret_1s_adj"] is None

def test_insufficient_exit_and_labels_reconcile(target_rows,tmp_path):
    out,_,_=generate_targets(*tables(target_rows),tconfig(tmp_path)); r=keyed(out)[(DATES[-2],"A")]
    assert r["fwd_open_to_close_ret_1s_adj"] is None
    assert r["target_null_reason_1s"]=="insufficient_future_sessions"
    for x in out.to_pylist():
        for h in (5,10,20):
            ret=x[f"fwd_open_to_close_ret_{h}s_adj"]
            assert x[f"up_{h}s"]==(None if ret is None else float(ret>0))

def test_future_append_and_input_order_invariance(target_rows,tmp_path):
    base,_,_=generate_targets(*tables(target_rows),tconfig(tmp_path)); old=keyed(base)
    extra=target_rows+[daily_row("2024-01-16","A",999,1000,True),daily_row("2024-01-16","B",1,1,True)]
    extended,_,_=generate_targets(*tables(list(reversed(extra))),tconfig(tmp_path)); new=keyed(extended)
    # Rows whose configured target end existed before append are invariant.
    for k,v in old.items():
        if v["target_end_date_1s"] is not None: assert new[k]["fwd_open_to_close_ret_1s_adj"]==v["fwd_open_to_close_ret_1s_adj"]

def test_pit_ranks_same_date_ties_and_ineligible_null(tmp_path):
    rows=[]
    for i,d in enumerate(DATES):
        rows += [daily_row(d,"A",100+i,101+i,True),daily_row(d,"B",100+i,101+i,True),daily_row(d,"C",200+i,201+i,False)]
    out,_,_=generate_targets(*tables(rows),tconfig(tmp_path)); last=[r for r in out.to_pylist() if r["trade_date"]==DATES[0]]
    a=next(r for r in last if r["symbol"]=="A"); b=next(r for r in last if r["symbol"]=="B"); c=next(r for r in last if r["symbol"]=="C")
    assert a["fwd_ret_5s_rank"]==b["fwd_ret_5s_rank"]==0.5
    assert c["fwd_ret_5s_rank"] is None
