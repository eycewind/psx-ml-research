import numpy as np
from psx_ml.c8.evaluation_train import _regime

def test_regime_thresholds_ignore_validation_values():
    train=np.array([1,1,1,0,0,0],bool); valid=~train
    a=np.array([1.,2.,3.,100.,200.,300.]); b=np.array([1.,2.,3.,-100.,-200.,-300.])
    _,qa=_regime(a,train,valid); _,qb=_regime(b,train,valid)
    assert qa==qb
