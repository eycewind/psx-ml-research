import hashlib
import sqlite3

import pytest

from psx_ml.data.sqlite import connect_readonly


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def test_opens_readonly_and_writes_fail_without_mutation(source_db):
    before=(digest(source_db),source_db.stat().st_size,source_db.stat().st_mtime_ns)
    with connect_readonly(source_db) as con:
        assert con.execute("PRAGMA query_only").fetchone()[0] == 1
        with pytest.raises(sqlite3.OperationalError): con.execute("INSERT INTO daily_ohlc(trade_date,symbol) VALUES ('x','y')")
        con.execute("PRAGMA query_only=OFF")
        with pytest.raises(sqlite3.OperationalError): con.execute("CREATE TABLE forbidden(x)")
    assert (digest(source_db),source_db.stat().st_size,source_db.stat().st_mtime_ns) == before


def test_missing_source_is_not_created(tmp_path):
    missing=tmp_path/"missing.db"
    with pytest.raises(FileNotFoundError):
        with connect_readonly(missing): pass
    assert not missing.exists()
