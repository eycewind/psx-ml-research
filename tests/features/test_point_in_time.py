import pyarrow as pa

from psx_ml.features.pipeline import compute_features
from tests.features.conftest import row,tables
from tests.features.test_price_and_quality import cfg


def as_rows(table,n=None):
    return table.slice(0,n).to_pylist() if n is not None else table.to_pylist()


def test_future_append_invariance(panel_rows,tmp_path):
    base,_,_=compute_features(*tables(panel_rows),cfg(tmp_path))
    future=panel_rows+[row("2024-02-01","AAA",999,999999,True),row("2024-02-01","BBB",1,1,False)]
    extended,_,_=compute_features(*tables(future),cfg(tmp_path))
    old={(r["trade_date"],r["symbol"]):r for r in base.to_pylist()}
    new={(r["trade_date"],r["symbol"]):r for r in extended.to_pylist()}
    assert all(new[k]==v for k,v in old.items())


def test_symbol_feature_isolation(panel_rows,tmp_path):
    base,_,_=compute_features(*tables(panel_rows),cfg(tmp_path))
    changed=[dict(r,close=r["close"]*3,close_adj=r["close"]*3) if r["symbol"]=="BBB" else r for r in panel_rows]
    other,_,_=compute_features(*tables(changed),cfg(tmp_path))
    symbol_features=[n for n in base.column_names if "rank" not in n and not n.startswith("market_") and n!="eligible_symbol_count"]
    assert [{k:r[k] for k in symbol_features} for r in base.to_pylist() if r["symbol"]=="AAA"] == [{k:r[k] for k in symbol_features} for r in other.to_pylist() if r["symbol"]=="AAA"]
