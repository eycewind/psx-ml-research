import numpy as np
import pytest
import torch
from psx_ml.tree_models.models import xgb_model,predict

pytestmark=pytest.mark.gpu

@pytest.mark.skipif(not torch.cuda.is_available(),reason="CUDA is not available")
def test_c9_xgboost_cuda_rank_regression():
    x=np.arange(80,dtype=float).reshape(40,2); y=np.linspace(0,1,40)
    model=xgb_model("regression",{"learning_rate":.05,"max_depth":3,"min_child_weight":1,"subsample":1.,"colsample_bytree":1.,"reg_alpha":0.,"reg_lambda":1.,"max_bin":64},42,8,1,"cuda")
    model.fit(x,y); prediction=predict(model,x,"regression")
    assert model.get_booster().save_config().find('"device":"cuda:0"')>=0
    assert np.isfinite(prediction).all() and np.std(prediction)>0
