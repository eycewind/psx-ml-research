import numpy as np
from psx_ml.c8.supplemental_metrics import rank_metrics

def test_rank_metrics_are_deterministic_and_finite():
    dates=["2024-01-01"]*10+["2024-01-02"]*10; symbols=[f"S{i:02}" for i in range(10)]*2
    y=np.tile(np.linspace(0,1,10),2); p=y.copy(); outcome=np.tile(np.arange(10),2)
    a,_,b=rank_metrics(y,outcome,p,dates,symbols,minimum=10,reps=20)
    c,_,_=rank_metrics(y,outcome,p,dates,symbols,minimum=10,reps=20)
    assert a==c and np.isclose(a["mean_daily_ic"],1) and np.isclose(a["ndcg_5"],1) and a["top_decile_capture"]==1
    assert a["d10_d1_spread"]==9 and np.isclose(a["bucket_monotonicity"],1) and len(b)==10

def test_rank_metrics_excludes_undersized_dates():
    m,_,_=rank_metrics([0,1],[0,1],[0,1],["d","d"],["a","b"],minimum=3,reps=5)
    assert m["finite_ic_date_count"]==0 and m["mean_daily_ic"] is None
