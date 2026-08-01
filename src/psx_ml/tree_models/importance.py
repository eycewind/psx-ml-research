from __future__ import annotations
import numpy as np
from sklearn.inspection import permutation_importance

def importance_rows(model,model_name,fold,target,features,xv,yv,kind,seed,sample_rows):
    rows=[]
    if model_name.startswith("lightgbm"):
        gain=model.booster_.feature_importance("gain"); split=model.booster_.feature_importance("split")
    elif model_name.startswith("xgboost"):
        score_gain=model.get_booster().get_score(importance_type="gain"); score_weight=model.get_booster().get_score(importance_type="weight")
        gain=np.array([score_gain.get(f"f{i}",0.) for i in range(len(features))]); split=np.array([score_weight.get(f"f{i}",0.) for i in range(len(features))])
    else: gain=np.zeros(len(features)); split=np.zeros(len(features))
    n=min(sample_rows,len(yv)); ix=np.linspace(0,len(yv)-1,n,dtype=int)
    scoring="neg_mean_squared_error" if kind=="regression" else "neg_log_loss"
    perm=permutation_importance(model,xv[ix],yv[ix],n_repeats=1,random_state=seed,scoring=scoring,n_jobs=1).importances_mean
    for i,f in enumerate(features): rows.append({"target_name":target,"fold_id":fold,"model_name":model_name,"feature":f,"gain_importance":float(gain[i]),"split_importance":float(split[i]),"permutation_importance":float(perm[i])})
    return rows
