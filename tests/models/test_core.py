import numpy as np
import pytest
from sklearn.metrics import r2_score

from psx_ml.models.baselines import classification_baselines,regression_baselines
from psx_ml.models.linear import fit_logistic,fit_ridge
from psx_ml.models.metrics import classification_metrics,date_block_interval,regression_metrics
from psx_ml.models.preprocessing import TrainOnlyPreprocessor
from psx_ml.models.validation import HoldoutLockedError,require_holdout_access

def test_train_only_preprocessing_ignores_validation_outlier_and_order():
    train=np.array([[1.,np.nan,5.],[3.,2.,5.],[2.,4.,5.]])
    a=TrainOnlyPreprocessor().fit(train); b=TrainOnlyPreprocessor().fit(train[::-1])
    np.testing.assert_allclose(a.medians,b.medians); np.testing.assert_allclose(a.means,b.means); np.testing.assert_allclose(a.scales,b.scales)
    before=a.state(["a","b","constant"]); a.transform(np.array([[1e99,1e99,5.]])); assert a.state(["a","b","constant"])==before
    assert a.constant==[2]

def test_all_missing_is_deterministic():
    p=TrainOnlyPreprocessor().fit(np.array([[np.nan,1],[np.nan,2]])); assert p.medians[0]==0 and p.all_missing==[0]

def test_baselines_and_hand_metrics_negative_r2():
    y=np.array([1.,2.,3.]); r=regression_baselines(y,2); np.testing.assert_array_equal(r["zero_return_baseline"],[0,0]); np.testing.assert_array_equal(r["training_mean_baseline"],[2,2])
    c=classification_baselines(np.array([0,1,1]),2); np.testing.assert_array_equal(c["majority_class_baseline"],[1,1]); np.testing.assert_allclose(c["training_prevalence_baseline"],2/3)
    m=regression_metrics(np.array([1.,2.]),np.array([0.,0.])); assert m["mae"]==1.5 and m["rmse"]==pytest.approx(np.sqrt(2.5)) and m["r2"]<0
    cm=classification_metrics(np.array([0,1]),np.array([.25,.75])); assert cm["brier"]==.0625 and cm["prevalence"]==.5 and cm["pr_auc"]==1

def test_linear_models_deterministic_and_shuffle_destroys_relation():
    x=np.arange(20,dtype=float).reshape(-1,1); y=2*x[:,0]+1
    model,_=fit_ridge(x,y,0.01); assert model.predict([[5]])[0]==pytest.approx(11,rel=1e-3)
    shuffled=np.random.default_rng(42).permutation(y); assert r2_score(y,model.predict(x))>r2_score(shuffled,model.predict(x))+.5
    yc=(x[:,0]>9).astype(int); a,_=fit_logistic(x,yc,1,500,42); b,_=fit_logistic(x,yc,1,500,42); np.testing.assert_allclose(a.predict_proba(x),b.predict_proba(x))

def test_holdout_lock_and_block_bootstrap():
    with pytest.raises(HoldoutLockedError): require_holdout_access(False)
    require_holdout_access(True)
    a=date_block_interval(["a","a","b","b"],[1,2,3,4],42,20); b=date_block_interval(["a","a","b","b"],[1,2,3,4],42,20); assert a==b
