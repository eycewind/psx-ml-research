from __future__ import annotations
import time,warnings
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier,HistGradientBoostingRegressor
import lightgbm as lgb
import xgboost as xgb

def hist_model(kind,params,seed,max_iter):
    cls=HistGradientBoostingRegressor if kind=="regression" else HistGradientBoostingClassifier
    return cls(**params,max_iter=max_iter,early_stopping=False,random_state=seed)

def lgb_model(kind,params,seed,rounds,threads):
    cls=lgb.LGBMRegressor if kind=="regression" else lgb.LGBMClassifier
    return cls(**params,n_estimators=rounds,random_state=seed,n_jobs=threads,deterministic=True,force_col_wise=True,verbosity=-1,bagging_freq=1)

def xgb_model(kind,params,seed,rounds,threads,device):
    cls=xgb.XGBRegressor if kind=="regression" else xgb.XGBClassifier
    objective="reg:squarederror" if kind=="regression" else "binary:logistic"
    return cls(**params,n_estimators=rounds,random_state=seed,n_jobs=threads,tree_method="hist",device=device,objective=objective,eval_metric="rmse" if kind=="regression" else "logloss")

def predict(model,x,kind): return model.predict(x) if kind=="regression" else model.predict_proba(x)[:,1]

def timed_fit_predict(model,xt,yt,xv,kind,fit_kwargs=None):
    start=time.perf_counter(); model.fit(xt,yt,**(fit_kwargs or {})); fit=time.perf_counter()-start
    start=time.perf_counter(); p=predict(model,xv,kind); pred=time.perf_counter()-start
    return model,np.asarray(p,float),fit,pred
