import sqlite3

from psx_ml.universe.point_in_time import build_point_in_time


def con_with(rows):
    con=sqlite3.connect(":memory:"); con.row_factory=sqlite3.Row
    con.execute("CREATE TABLE daily_ohlc(trade_date TEXT,symbol TEXT,close REAL,volume INTEGER)")
    con.executemany("INSERT INTO daily_ohlc VALUES (?,?,?,?)",rows)
    return con


def compute(rows):
    con=con_with(rows)
    result=list(build_point_in_time(con,3,2,50,1.0)); con.close(); return result


def test_future_row_cannot_change_past_eligibility():
    past=[("2024-01-01","A",10,10),("2024-01-02","A",11,10)]
    before=compute(past)
    after=compute(past+[("2024-01-03","A",1000,1000000)])
    assert before == after[:len(before)]
    assert before[-1]["eligible"]
    assert all(r["window_end"] == r["trade_date"] for r in after)
