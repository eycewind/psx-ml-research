import hashlib,json
from pathlib import Path
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

@pytest.fixture
def model_project(tmp_path):
    n_dates=40; syms=["A","B","C"]; rows=[]
    for d in range(n_dates):
        for j,s in enumerate(syms):
            f1=(d+j)/20; f2=np.sin(d+j); ret=.02*f1-.03*f2; up=float(ret>0)
            rows.append((f"2024-01-{d+1:02d}",s,True,f1,f2,ret,ret*1.2,ret*1.5,up,up,up))
    names=["trade_date","symbol","point_in_time_eligible","f1","f2","fwd_open_to_close_ret_5s_adj","fwd_open_to_close_ret_10s_adj","fwd_open_to_close_ret_20s_adj","up_5s","up_10s","up_20s"]
    labelled=pa.table({k:[r[i] for r in rows] for i,k in enumerate(names)})
    folds=[]
    for fold,vs,ve in (("f1",20,29),("f2",30,39)):
        for i,r in enumerate(rows):
            d=i//3; role="train" if d<vs else ("validation" if d<=ve else "not_in_fold")
            folds.append((r[0],r[1],fold,role))
    splits=pa.table({"trade_date":[x[0] for x in folds],"symbol":[x[1] for x in folds],"fold_id":[x[2] for x in folds],"split_role":[x[3] for x in folds]})
    data=tmp_path/"data"; art=tmp_path/"art"; data.mkdir(); art.mkdir(); lp=data/"label.parquet"; sp=data/"splits.parquet"; pq.write_table(labelled,lp); pq.write_table(splits,sp)
    c4={"output":{"labelled":{"file_sha256":sha(lp)},"splits":{"file_sha256":sha(sp)}}}; c3={"ordered_features":["f1","f2"]}; c2={"manifest_version":1}
    for name,obj in (("c4.json",c4),("c3.json",c3),("c2.json",c2)): (art/name).write_text(json.dumps(obj))
    cfg=tmp_path/"models.toml"; cfg.write_text('''[input]\nlabelled_path="data/label.parquet"\nsplit_path="data/splits.parquet"\nc4_manifest_path="art/c4.json"\nc3_manifest_path="art/c3.json"\nc2_manifest_path="art/c2.json"\n[output]\npredictions_path="out/pred.parquet"\ncoefficients_path="out/coef.parquet"\nmanifest_path="out/manifest.json"\nmodel_report_path="art/model.md"\ncoefficient_report_path="art/coef.md"\n[model_set]\nname="test"\nversion=1\nseed=42\nridge_alphas=[0.1,1.0]\nlogistic_cs=[0.1,1.0]\nlogistic_max_iter=200\nbootstrap_replicates=20\nfeatures=["f1","f2"]\nregression_targets=["fwd_open_to_close_ret_5s_adj","fwd_open_to_close_ret_10s_adj","fwd_open_to_close_ret_20s_adj"]\nclassification_targets=["up_5s","up_10s","up_20s"]\n''')
    return tmp_path,cfg
