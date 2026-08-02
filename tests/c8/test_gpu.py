import numpy as np
import pytest
import torch
from psx_ml.tree_models.models import xgb_model

pytestmark=pytest.mark.gpu

@pytest.mark.skipif(not torch.cuda.is_available(),reason="CUDA is not available")
def test_c8_xgboost_cuda_regression():
    rng=np.random.default_rng(42); x=rng.normal(size=(512,12)); y=x[:,0]*.1-x[:,1]*.05
    params={"learning_rate":.03,"max_depth":3,"min_child_weight":20,"subsample":.9,"colsample_bytree":.9,"reg_alpha":.1,"reg_lambda":10.,"max_bin":128}
    model=xgb_model("regression",params,42,8,1,"cuda").fit(x,y); p=model.predict(x)
    assert np.isfinite(p).all() and np.std(p)>0

