import sqlite3

import pytest


COLUMNS="""trade_date TEXT, symbol TEXT, sector TEXT, open REAL, high REAL, low REAL,
close REAL, volume INTEGER, ldcp REAL, open_missing INTEGER, source TEXT,
open_adj REAL, high_adj REAL, low_adj REAL, close_adj REAL, volume_adj REAL,
adj_factor REAL"""


@pytest.fixture
def source_db(tmp_path):
    path=tmp_path/"source.db"
    con=sqlite3.connect(path)
    con.execute(f"CREATE TABLE daily_ohlc ({COLUMNS})")
    rows=[
      ("2024-01-01","AAA","01",10,11,9,10,100000,9.5,0,"test",5,5.5,4.5,5,200000,.5),
      ("2024-01-02","AAA","01",None,11,9,10,0,10,1,"test",None,5.5,4.5,5,0,.5),
      ("bad-date","BAD","01",12,11,9,12,None,10,0,"test",12,11,9,99,None,1),
      ("2024-01-01","AAA","01",10,11,9,10,100000,9.5,0,"duplicate",5,5.5,4.5,5,200000,.5),
    ]
    con.executemany("INSERT INTO daily_ohlc VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",rows)
    con.commit(); con.close()
    return path
