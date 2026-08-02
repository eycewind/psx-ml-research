import numpy as np
from psx_ml.c8.evaluation_metrics import aggregate_folds,evaluate_predictions

def test_buckets_daily_ic_and_bootstrap_are_deterministic():
    dates=["a"]*20+["b"]*20; symbols=[str(i) for i in range(20)]*2; y=np.arange(40,dtype=float); p=y.copy()
    a=evaluate_predictions(y,p,dates,symbols,42,20,10); b=evaluate_predictions(y,p,dates,symbols,42,20,10)
    assert a[0]==b[0] and a[0]["mean_daily_ic"]==1 and a[0]["d10_d1_mean_spread"]>0
    assert sum(r["row_count"] for r in a[2])==40

def test_undefined_ic_is_counted_not_zeroed():
    m,_,_,_=evaluate_predictions(np.arange(20),np.ones(20),["a"]*20,[str(i) for i in range(20)],42,10,10)
    assert m["finite_ic_date_count"]==0 and m["constant_prediction_date_count"]==1 and m["mean_daily_ic"] is None

def test_fold_aggregation_retains_stability():
    base={"stage":1,"horizon":5,"target_family":"x","feature_variant":"A","model_name":"m","comparison_subset":"natural","finite_ic_date_count":2,"population_eligible_date_count":3,"d10_d1_mean_spread":.1}
    rows=[{**base,"mean_daily_ic":.2},{**base,"mean_daily_ic":-.1}]
    a=aggregate_folds(rows)[0]; assert a["positive_ic_folds"]==1 and a["undefined_ic_dates"]==2
