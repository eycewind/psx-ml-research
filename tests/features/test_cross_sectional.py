from psx_ml.features.pipeline import compute_features
from tests.features.conftest import row,tables
from tests.features.test_price_and_quality import cfg


def test_date_isolation_ties_and_eligible_population(tmp_path):
    rows=[]
    for day in range(1,23):
        d=f"2024-01-{day:02d}"
        for sym,mult in (("A",1),("B",1),("C",2)):
            rows.append(row(d,sym,100+day*mult,100*mult,eligible=sym!="C"))
    table,_,_=compute_features(*tables(list(reversed(rows))),cfg(tmp_path))
    last=[r for r in table.to_pylist() if r["trade_date"]=="2024-01-22"]
    a=next(r for r in last if r["symbol"]=="A"); b=next(r for r in last if r["symbol"]=="B"); c=next(r for r in last if r["symbol"]=="C")
    assert a["ret_20obs_rank_adj"]==b["ret_20obs_rank_adj"]==0.5
    assert c["ret_20obs_rank_adj"] is None
    assert a["eligible_symbol_count"]==b["eligible_symbol_count"]==2
