import numpy as np
import pyarrow as pa
from psx_ml.tree_models.datasets import canonical_mask,inner_chronological
from psx_ml.tree_models.models import hist_model,lgb_model,predict,xgb_model
from psx_ml.tree_models.metrics import quantile_spread,daily_ic_metrics
from psx_ml.tree_models.pipeline import _aggregate

def test_universe_filter_and_inner_chronology():
    labelled=pa.Table.from_pylist([{"trade_date":"2024-01-01","symbol":"A"},{"trade_date":"2024-01-02","symbol":"A"},{"trade_date":"2024-01-03","symbol":"B"}])
    universe=pa.Table.from_pylist([{"trade_date":"2024-01-01","symbol":"A","universe_name":"u","eligible":True,"instrument_type":"ordinary_equity"},{"trade_date":"2024-01-02","symbol":"A","universe_name":"u","eligible":False,"instrument_type":"ordinary_equity"},{"trade_date":"2024-01-03","symbol":"B","universe_name":"u","eligible":True,"instrument_type":"debt_security"}])
    assert canonical_mask(labelled,universe,"u").tolist()==[True,False,False]
    dates=np.array([f"2024-01-{x:02d}" for x in range(1,11)],object); tr,va,b=inner_chronological(dates,np.ones(10,bool),.2)
    assert max(dates[tr])<min(dates[va]) and b=="2024-01-09"

def test_tree_models_finite_probabilities_and_determinism():
    rng=np.random.default_rng(42); x=rng.normal(size=(200,4)); x[::17,0]=np.nan; y=np.nan_to_num(x[:,1])+.2*rng.normal(size=200); c=(y>0).astype(int)
    h=hist_model("regression",{"learning_rate":.05,"max_leaf_nodes":15,"max_depth":4,"min_samples_leaf":20,"l2_regularization":1.},42,30).fit(x,y)
    assert np.isfinite(h.predict(x)).all()
    l=lgb_model("classification",{"learning_rate":.05,"num_leaves":15,"max_depth":4,"min_child_samples":20,"feature_fraction":1.,"bagging_fraction":1.,"reg_alpha":0.,"reg_lambda":1.,"max_bin":63},42,30,1).fit(x,c)
    p=predict(l,x,"classification"); assert np.all((p>=0)&(p<=1)) and np.std(p)>0
    a=xgb_model("regression",{"learning_rate":.05,"max_depth":3,"min_child_weight":1,"subsample":1.,"colsample_bytree":1.,"reg_alpha":0.,"reg_lambda":1.,"max_bin":64},42,20,1,"cpu").fit(x,y).predict(x)
    b=xgb_model("regression",{"learning_rate":.05,"max_depth":3,"min_child_weight":1,"subsample":1.,"colsample_bytree":1.,"reg_alpha":0.,"reg_lambda":1.,"max_bin":64},42,20,1,"cpu").fit(x,y).predict(x)
    assert np.allclose(a,b)

def test_quantile_ties_are_symbol_deterministic():
    one=quantile_spread(["d"]*10,list("JIHGFEDCBA"),np.arange(10),np.ones(10),q=5,minimum=10)
    two=quantile_spread(["d"]*10,list("ABCDEFGHIJ"),np.arange(9,-1,-1),np.ones(10),q=5,minimum=10)
    assert one==two

def test_daily_ic_normal_finite():
    m=daily_ic_metrics(["a"]*4+["b"]*4,[1,2,3,4]*2,[1,2,3,4,4,3,2,1],4)
    assert m["finite_ic_date_count"]==2 and m["mean_daily_ic"]==0 and m["positive_ic_fraction"]==.5

def test_daily_ic_all_undefined_constant_predictions_and_targets():
    m=daily_ic_metrics(["a"]*4+["b"]*4,[1,2,3,4]+[1]*4,[1]*4+[1,2,3,4],4)
    assert m["constant_prediction_date_count"]==1 and m["constant_target_date_count"]==1
    assert m["finite_ic_date_count"]==0 and m["mean_daily_ic"] is None

def test_daily_ic_mixed_counts_are_deterministic():
    args=(["small"]*2+["finite"]*4+["constant"]*4,[1,2]+[1,2,3,4]+[1,2,3,4],[1,2]+[4,3,2,1]+[1]*4)
    a=daily_ic_metrics(*args,minimum=4)
    assert a==daily_ic_metrics(*args,minimum=4) and a["validation_date_count"]==3
    assert a["population_eligible_date_count"]==2 and a["finite_ic_date_count"]==1 and a["mean_daily_ic"]==-1

def test_fold_aggregation_uses_only_finite_values():
    metrics={"t:f1:m":{"n":2,"mean_daily_ic":.2},"t:f2:m":{"n":3,"mean_daily_ic":float("nan")},"t:f3:m":{"n":4,"mean_daily_ic":.4}}
    a=_aggregate(metrics)["t:m"]
    assert np.isclose(a["mean"]["mean_daily_ic"],.3) and a["finite_fold_counts"]["mean_daily_ic"]==2
