import numpy as np
import pytest
import torch
from psx_ml.tree_models.models import xgb_model

pytestmark=pytest.mark.gpu

@pytest.mark.skipif(not torch.cuda.is_available(),reason="CUDA is not available")
def test_c7_xgboost_cuda_fit_and_probability_bounds():
    rng=np.random.default_rng(42); x=rng.normal(size=(512,6)); y=(x[:,0]+x[:,1]>0).astype(int)
    model=xgb_model("classification",{"learning_rate":.05,"max_depth":3,"min_child_weight":1,"subsample":1.,"colsample_bytree":1.,"reg_alpha":0.,"reg_lambda":1.,"max_bin":64},42,8,1,"cuda")
    model.fit(x,y); p=model.predict_proba(x)[:,1]
    assert model.get_booster().attributes().get("device") in (None,"cuda:0")
    assert np.isfinite(p).all() and np.all((p>=0)&(p<=1)) and np.std(p)>0
