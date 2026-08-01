import hashlib,json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from psx_ml.targets.config import TargetConfig,SplitConfig,FoldConfig

DATES=[f"2024-01-{d:02d}" for d in range(1,16)]

def daily_row(d,s,o,c,eligible=True):
    return {"trade_date":d,"symbol":s,"open_adj":o,"close_adj":c,"eligible":eligible}

@pytest.fixture
def target_rows():
    rows=[]
    for i,d in enumerate(DATES):
        rows.append(daily_row(d,"A",100+i,101+i,True))
        rows.append(daily_row(d,"B",50+i,51+i,i>=2))
    # C is absent on exact next session after Jan 1 and has an invalid later open.
    rows += [daily_row(DATES[0],"C",10,10,True),daily_row(DATES[2],"C",0,12,True),daily_row(DATES[3],"C",13,13,True)]
    return rows

def tables(rows):
    daily=pa.table({k:[r[k] for r in rows] for k in ("trade_date","symbol","open_adj","close_adj")})
    features=pa.table({"trade_date":[r["trade_date"] for r in rows],"symbol":[r["symbol"] for r in rows],
      "point_in_time_eligible":[r["eligible"] for r in rows],"dummy_feature":[1.0]*len(rows)})
    return features,daily

def tconfig(tmp_path,minpop=2):
    p=Path(tmp_path)/"x"
    return TargetConfig(p,p,p,p,p,p,"test",1,"adjusted",(1,5,10,20),(5,10,20),(5,20),minpop,20)

def sconfig(tmp_path):
    p=Path(tmp_path)/"x"
    return SplitConfig(p,p,p,p,"test_splits",1,2,"2024-01-13","2024-01-15",
      (FoldConfig("fold","2024-01-01","2024-01-08","2024-01-10"),))

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def write_pipeline_inputs(root,rows):
    features,daily=tables(rows); (root/"data").mkdir(); (root/"artifacts").mkdir()
    fp=root/"data/features.parquet"; dp=root/"data/daily.parquet"; pq.write_table(features,fp); pq.write_table(daily,dp)
    fm={"manifest_version":1,"output":{"file_sha256":sha(fp),"rows":features.num_rows,"logical_content_sha256":"synthetic"}}
    c1={"manifest_version":1,"source_row_count":daily.num_rows,"maximum_source_trade_date":max(r["trade_date"] for r in rows),"outputs":{"daily":{"sha256":sha(dp)}}}
    fmp=root/"artifacts/C3.json"; c1p=root/"artifacts/C1.json"; fmp.write_text(json.dumps(fm)); c1p.write_text(json.dumps(c1))
    tc=root/"targets.toml"; tc.write_text('''[input]\nfeature_path="data/features.parquet"\nfeature_manifest_path="artifacts/C3.json"\ndaily_path="data/daily.parquet"\nc1_manifest_path="artifacts/C1.json"\n[output]\nlabelled_path="data/out/targets.parquet"\ntarget_manifest_path="data/out/target_manifest.json"\n[targets]\nname="synthetic"\nversion=1\nprice_family="adjusted"\nhorizons=[1,5,10,20]\nclassification_horizons=[5,10,20]\nrank_horizons=[5,20]\nminimum_rank_population=2\nprimary_horizon=20\n''')
    sc=root/"splits.toml"; sc.write_text('''[output]\nassignment_path="data/out/splits.parquet"\nmanifest_path="data/out/manifest.json"\ntarget_report_path="artifacts/target.md"\nsplit_report_path="artifacts/split.md"\n[splits]\nname="synthetic"\nversion=1\nembargo_sessions=2\nfinal_test_start="2024-01-13"\nfinal_test_end="2024-01-15"\n[[folds]]\nid="fold"\ntrain_start="2024-01-01"\nvalidation_start="2024-01-08"\nvalidation_end="2024-01-10"\n''')
    return tc,sc
