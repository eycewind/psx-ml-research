import sqlite3

from psx_ml.runtime.config import RuntimeConfig
from psx_ml.runtime.diagnostics import diagnose
from psx_ml.runtime.reproducibility import configure_reproducibility


def test_runtime_never_opens_sqlite(monkeypatch,tmp_path):
    calls=[]
    monkeypatch.setattr(sqlite3,"connect",lambda *a,**k:calls.append((a,k)))
    configure_reproducibility(42)
    diagnose(RuntimeConfig(device="cpu"),tmp_path)
    assert calls == []
