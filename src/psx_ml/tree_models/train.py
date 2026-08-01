from __future__ import annotations
from collections import defaultdict
import numpy as np
import pyarrow as pa
import lightgbm as lgb
from .datasets import canonical_mask,fold_roles,inner_chronological,matrix
from .importance import importance_rows
from .metrics import classification,regression,selection_loss
from .models import hist_model,lgb_model,predict,timed_fit_predict,xgb_model

def _rows(dates,symbols,fold,target,y,p,model,device,kind):
    return [{"trade_date":d,"symbol":s,"fold_id":fold,"split_role":"validation","universe_name":"pit_liquid_ordinary_equity_v1","target_name":target,"target":float(a),"prediction":float(b>=.5) if kind=="classification" else float(b),"prediction_probability":float(b) if kind=="classification" else None,"model_name":model,"model_version":1,"device":device} for d,s,a,b in zip(dates,symbols,y,p)]

def _prediction_diagnostics(p,kind):
    p=np.asarray(p,float)
    out={"prediction_mean":float(np.mean(p)),"prediction_std":float(np.std(p)),"prediction_min":float(np.min(p)),"prediction_max":float(np.max(p)),"unique_prediction_count":int(np.unique(np.round(p,12)).size),"constant_or_near_constant_prediction":bool(np.ptp(p)<=1e-12 or np.std(p)<=1e-10)}
    if kind=="classification": out.update({"classification_probability_mean":float(np.mean(p)),"classification_probability_std":float(np.std(p)),"classification_probability_min":float(np.min(p)),"classification_probability_max":float(np.max(p))})
    else: out.update({"classification_probability_mean":None,"classification_probability_std":None,"classification_probability_min":None,"classification_probability_max":None})
    return out

def _lgb_stopping(model,kind):
    metric="l2" if kind=="regression" else "binary_logloss"; vals=model.evals_result_.get("valid_0",{}).get(metric,[]); best=int(model.best_iteration_ or len(vals) or 1)
    return {"best_iteration":best,"early_stopping_reference_metric":metric,"best_inner_validation_score":float(vals[best-1]) if vals and best<=len(vals) else None,"first_iteration_score":float(vals[0]) if vals else None,"last_evaluated_iteration":len(vals)}

def _xgb_stopping(model,kind):
    metric="rmse" if kind=="regression" else "logloss"; vals=model.evals_result()["validation_0"][metric]
    return {"best_iteration":int(model.best_iteration+1),"early_stopping_reference_metric":metric,"best_inner_validation_score":float(model.best_score),"first_iteration_score":float(vals[0]),"last_evaluated_iteration":len(vals)}

def evaluate(labelled,splits,universe,cfg):
    m=cfg.model; features=m["features"]; x=matrix(labelled,features); dates=np.array(labelled["trade_date"].to_pylist(),object); symbols=np.array(labelled["symbol"].to_pylist(),object)
    canonical=canonical_mask(labelled,universe,m["canonical_universe"]); roles=fold_roles(labelled,splits); folds=sorted(roles)
    predictions=[]; importance=[]; metrics={}; runtimes=[]; selections={}; warnings=[]
    tasks=[("regression",t) for t in m["regression_targets"]]+[("classification",t) for t in m["classification_targets"]]
    for kind,target in tasks:
        y=np.asarray(labelled[target].to_numpy(zero_copy_only=False),float); history=defaultdict(list)
        for fold_index,fold in enumerate(folds):
            role=roles[fold]; train=(role=="train")&canonical&np.isfinite(y); valid=(role=="validation")&canonical&np.isfinite(y)
            it,iv,boundary=inner_chronological(dates,train,m["inner_validation_fraction"])
            prior={i:np.mean(v) for i,v in history.items() if v}; selected_idx=0 if not prior else min(prior,key=lambda i:(prior[i],i))
            candidate_results={}
            for i,params in enumerate(m["lightgbm_candidates"]):
                clean={k:v for k,v in params.items() if k!="name"}; inner=lgb_model(kind,clean,m["seed"],m["boosting_max_rounds"],m["threads"])
                inner.fit(x[it],y[it],eval_set=[(x[iv],y[iv])],callbacks=[lgb.early_stopping(m["early_stopping_rounds"],verbose=False)])
                stopping=_lgb_stopping(inner,kind); rounds=max(1,int(inner.best_iteration_ or m["boosting_max_rounds"])); model=lgb_model(kind,clean,m["seed"],rounds,m["threads"])
                model,p,fit_time,pred_time=timed_fit_predict(model,x[train],y[train],x[valid],kind)
                met=regression(y[valid],p,dates[valid],symbols[valid],m["seed"],m["bootstrap_replicates"]) if kind=="regression" else classification(y[valid],p,dates[valid],m["seed"],m["bootstrap_replicates"])
                candidate_results[i]=(model,p,met,rounds,fit_time,pred_time,stopping); history[i].append(selection_loss(kind,met))
            model,p,met,rounds,fit_time,pred_time,stopping=candidate_results[selected_idx]; name="lightgbm_cpu"
            predictions.extend(_rows(dates[valid],symbols[valid],fold,target,y[valid],p,name,"cpu",kind)); metrics[f"{target}:{fold}:{name}"]=met
            importance.extend(importance_rows(model,name,fold,target,features,x[valid],y[valid],kind,m["seed"],m["permutation_sample_rows"])); runtimes.append({"target":target,"fold":fold,"model":name,"device":"cpu","fit_seconds":fit_time,"predict_seconds":pred_time,"rounds":rounds,"train_rows":int(train.sum()),"validation_rows":int(valid.sum()),"features":len(features),"threads":m["threads"],**stopping,**_prediction_diagnostics(p,kind)})
            selections[f"{target}:{fold}"]={"candidate_index":selected_idx,"candidate_name":m["lightgbm_candidates"][selected_idx]["name"],"evidence_folds":folds[:fold_index],"inner_boundary":boundary,"rounds":rounds}
            hp=hist_model(kind,m["hist_default"],m["seed"],m["hist_max_iter"]); hp,pp,ft,pt=timed_fit_predict(hp,x[train],y[train],x[valid],kind); hn="hist_gradient_boosting_cpu"
            hm=regression(y[valid],pp,dates[valid],symbols[valid],m["seed"],m["bootstrap_replicates"]) if kind=="regression" else classification(y[valid],pp,dates[valid],m["seed"],m["bootstrap_replicates"])
            predictions.extend(_rows(dates[valid],symbols[valid],fold,target,y[valid],pp,hn,"cpu",kind)); metrics[f"{target}:{fold}:{hn}"]=hm; runtimes.append({"target":target,"fold":fold,"model":hn,"device":"cpu","fit_seconds":ft,"predict_seconds":pt,"rounds":m["hist_max_iter"],"train_rows":int(train.sum()),"validation_rows":int(valid.sum()),"features":len(features),"threads":m["threads"],"best_iteration":m["hist_max_iter"],"early_stopping_reference_metric":None,"best_inner_validation_score":None,"first_iteration_score":None,"last_evaluated_iteration":m["hist_max_iter"],**_prediction_diagnostics(pp,kind)})
            clean=m["xgboost_default"]; inner=xgb_model(kind,clean,m["seed"],m["boosting_max_rounds"],m["threads"],"cuda"); inner.set_params(early_stopping_rounds=m["early_stopping_rounds"])
            inner.fit(x[it],y[it],eval_set=[(x[iv],y[iv])],verbose=False); stopping=_xgb_stopping(inner,kind); xr=max(1,int(inner.best_iteration+1)); xm=xgb_model(kind,clean,m["seed"],xr,m["threads"],"cuda")
            xm,xp,ft,pt=timed_fit_predict(xm,x[train],y[train],x[valid],kind); xn="xgboost_gpu"
            xmet=regression(y[valid],xp,dates[valid],symbols[valid],m["seed"],m["bootstrap_replicates"]) if kind=="regression" else classification(y[valid],xp,dates[valid],m["seed"],m["bootstrap_replicates"])
            predictions.extend(_rows(dates[valid],symbols[valid],fold,target,y[valid],xp,xn,"cuda",kind)); metrics[f"{target}:{fold}:{xn}"]=xmet
            importance.extend(importance_rows(xm,xn,fold,target,features,x[valid],y[valid],kind,m["seed"],m["permutation_sample_rows"])); runtimes.append({"target":target,"fold":fold,"model":xn,"device":"cuda","fit_seconds":ft,"predict_seconds":pt,"rounds":xr,"train_rows":int(train.sum()),"validation_rows":int(valid.sum()),"features":len(features),"threads":m["threads"],**stopping,**_prediction_diagnostics(xp,kind)})
    return pa.Table.from_pylist(predictions),pa.Table.from_pylist(importance),{"metrics":metrics,"runtimes":runtimes,"selections":selections,"warnings":warnings}
