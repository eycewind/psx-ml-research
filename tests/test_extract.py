import json

import pyarrow.parquet as pq

from psx_ml.data.extract import export_daily, sha256_file
from psx_ml.data.sqlite import connect_readonly


COLS=["trade_date","symbol","sector","open","high","low","close","volume","ldcp","open_missing","source","open_adj","high_adj","low_adj","close_adj","volume_adj","adj_factor"]


def test_same_snapshot_has_deterministic_parquet_and_reconciles(source_db,tmp_path):
    a=tmp_path/"a.parquet"; b=tmp_path/"b.parquet"
    with connect_readonly(source_db) as con:
        na,sql=export_daily(con,COLS,a)
        nb,_=export_daily(con,COLS,b)
        stats=dict(con.execute("SELECT COUNT(*) rows,COUNT(DISTINCT symbol) symbols,MIN(trade_date) min_date,MAX(trade_date) max_date FROM daily_ohlc").fetchone())
    assert na == nb == stats["rows"] == pq.read_metadata(a).num_rows
    assert sha256_file(a) == sha256_file(b)
    table=pq.read_table(a,columns=["trade_date","symbol"])
    assert len(set(table.column("symbol").to_pylist())) == stats["symbols"]
    assert "ORDER BY trade_date,symbol" in sql
