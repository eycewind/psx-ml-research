import hashlib
import json

import pyarrow as pa
import pyarrow.parquet as pq
import pytest


def row(date,symbol,close,volume=100.0,eligible=True,open_=None,high=None,low=None):
    open_=close if open_ is None else open_; high=close+1 if high is None else high; low=close-1 if low is None else low
    return {"trade_date":date,"symbol":symbol,"open":open_,"high":high,"low":low,"close":close,"volume":volume,
      "open_adj":open_,"high_adj":high,"low_adj":low,"close_adj":close,"volume_adj":volume,"adj_factor":1.0,"eligible":eligible}


@pytest.fixture
def panel_rows():
    rows=[]
    for day in range(1,26):
        d=f"2024-01-{day:02d}"
        rows.append(row(d,"AAA",100+day,1000+day,eligible=day>=3))
        if day not in (4,9): rows.append(row(d,"BBB",50+day*2,500+day,eligible=day>=5))
    rows.append(row("2024-01-10","CCC",10,0,eligible=False,open_=12,high=11,low=9))
    rows.append(row("2024-01-11","CCC",10,None,eligible=False,high=8,low=9))
    return rows


def tables(rows):
    daily=pa.table({k:[r[k] for r in rows] for k in ("trade_date","symbol","open","high","low","close","volume","open_adj","high_adj","low_adj","close_adj","volume_adj","adj_factor")})
    universe=pa.table({"trade_date":[r["trade_date"] for r in rows],"symbol":[r["symbol"] for r in rows],"eligible":[r["eligible"] for r in rows]})
    return daily,universe


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def write_inputs(root,rows):
    daily,universe=tables(rows); cache=root/"data/cache"; reports=root/"artifacts/reports"; cache.mkdir(parents=True); reports.mkdir(parents=True)
    dp=cache/"daily.parquet"; up=cache/"universe.parquet"; pq.write_table(daily,dp); pq.write_table(universe,up)
    dates=[r["trade_date"] for r in rows]; symbols={r["symbol"] for r in rows}
    manifest={"manifest_version":1,"source_row_count":len(rows),"symbol_count":len(symbols),"date_range":{"min":min(dates),"max":max(dates)},
      "maximum_source_trade_date":max(dates),"outputs":{"daily":{"sha256":sha(dp)},"point_in_time_universe":{"sha256":sha(up)}}}
    mp=reports/"C1.json"; mp.write_text(json.dumps(manifest))
    cfg=root/"features.toml"; cfg.write_text('''[input]\ndaily_path="data/cache/daily.parquet"\nuniverse_path="data/cache/universe.parquet"\nmanifest_path="artifacts/reports/C1.json"\n[output]\nfeature_path="data/processed/features.parquet"\nmanifest_path="data/processed/manifest.json"\nreport_path="artifacts/reports/C3.md"\n[fields]\nprice_family="adjusted"\nvolume_family="adjusted"\n[windows]\nreturns=[1,5,20]\nrolling=[5,20,60]\n[quality]\nminimum_history=20\nstale_run_threshold=5\nminimum_cross_section_size=2\n[execution]\nengine="cpu"\nfloat_precision="float64"\n''')
    return cfg
