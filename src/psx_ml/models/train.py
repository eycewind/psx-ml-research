from __future__ import annotations
from collections import defaultdict
from itertools import chain
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc

from .baselines import classification_baselines,regression_baselines
from .linear import fit_logistic,fit_ridge
from .metrics import classification_metrics,date_block_interval,regression_metrics
from .preprocessing import TrainOnlyPreprocessor

def _matrix(table,features): return np.column_stack([np.asarray(table[f].to_numpy(zero_copy_only=False),dtype=float) for f in features])

def fold_roles(splits,labelled):
    result={}; fold_ids=sorted(set(splits["fold_id"].to_pylist())); lk=list(zip(labelled["trade_date"].to_pylist(),labelled["symbol"].to_pylist()))
    for fold in fold_ids:
        part=splits.filter(pc.equal(splits["fold_id"],fold)); keys=list(zip(part["trade_date"].to_pylist(),part["symbol"].to_pylist()))
        if keys!=lk: raise ValueError(f"C4 split keys/order do not reconcile for {fold}")
        result[fold]=np.array(part["split_role"].to_pylist(),dtype=object)
    return result

def _pred_rows(dates,symbols,fold,target,y,p,model,kind):
    n=len(y); return {"trade_date":dates.tolist(),"symbol":symbols.tolist(),"fold_id":[fold]*n,"split_role":["validation"]*n,
      "target_name":[target]*n,"target":y.tolist(),"prediction":((p>=.5).astype(float) if kind=="classification" else p).tolist(),
      "prediction_probability":(p.tolist() if kind=="classification" else [None]*n),"model_name":[model]*n,"model_version":[1]*n}

def evaluate(labelled,splits,config):
    xall=_matrix(labelled,config.features); dates=np.array(labelled["trade_date"].to_pylist(),dtype=object); symbols=np.array(labelled["symbol"].to_pylist(),dtype=object)
    eligible=np.asarray(labelled["point_in_time_eligible"].to_numpy(zero_copy_only=False),dtype=bool); roles=fold_roles(splits,labelled)
    predictions=[]; coefficient_rows=[]; metrics={}; preprocessing={}; selected={}; warnings_out={}; bootstrap={}
    tasks=[("regression",t) for t in config.regression_targets]+[("classification",t) for t in config.classification_targets]
    for kind,target in tasks:
        yall=np.asarray(labelled[target].to_numpy(zero_copy_only=False),dtype=float); grid=config.ridge_alphas if kind=="regression" else config.logistic_cs
        grid_scores=defaultdict(list); fold_cache={}
        for fold,role in roles.items():
            tr=(role=="train")&eligible&np.isfinite(yall); va=(role=="validation")&eligible&np.isfinite(yall)
            pre=TrainOnlyPreprocessor().fit(xall[tr]); xt,xv=pre.transform(xall[tr]),pre.transform(xall[va]); yt,yv=yall[tr],yall[va]
            fold_cache[fold]=(tr,va,pre,xt,xv,yt,yv); preprocessing[f"{target}:{fold}"]=pre.state(config.features)
            for hp in grid:
                model,w=(fit_ridge(xt,yt,hp) if kind=="regression" else fit_logistic(xt,yt,hp,config.logistic_max_iter,config.seed))
                p=model.predict(xv) if kind=="regression" else model.predict_proba(xv)[:,1]
                score=regression_metrics(yv,p)["rmse"] if kind=="regression" else classification_metrics(yv,p)["log_loss"]
                grid_scores[float(hp)].append(score); warnings_out[f"{target}:{fold}:{hp}"]=w
        chosen=min(grid,key=lambda hp:(np.mean(grid_scores[float(hp)]),hp)); selected[target]={"parameter":"alpha" if kind=="regression" else "C","value":float(chosen),"validation_scores":{str(k):v for k,v in grid_scores.items()}}
        for fold,(tr,va,pre,xt,xv,yt,yv) in fold_cache.items():
            base=regression_baselines(yt,len(yv)) if kind=="regression" else classification_baselines(yt,len(yv))
            fixed=1.0
            fitted=[]
            for model_name,hp in (("ridge_fixed_alpha_1" if kind=="regression" else "logistic_fixed_c_1",fixed),("ridge_selected" if kind=="regression" else "logistic_selected",chosen)):
                model,w=(fit_ridge(xt,yt,hp) if kind=="regression" else fit_logistic(xt,yt,hp,config.logistic_max_iter,config.seed))
                p=model.predict(xv) if kind=="regression" else model.predict_proba(xv)[:,1]; fitted.append((model_name,model,p,w))
            for model_name,p in base.items():
                metric=regression_metrics(yv,p) if kind=="regression" else classification_metrics(yv,p); metrics[f"{target}:{fold}:{model_name}"]=metric
                predictions.append(_pred_rows(dates[va],symbols[va],fold,target,yv,p,model_name,kind))
            for model_name,model,p,w in fitted:
                metric=regression_metrics(yv,p) if kind=="regression" else classification_metrics(yv,p); metrics[f"{target}:{fold}:{model_name}"]=metric
                predictions.append(_pred_rows(dates[va],symbols[va],fold,target,yv,p,model_name,kind))
                coef=model.coef_.reshape(-1)
                for rank,j in enumerate(np.argsort(-np.abs(coef)),1):
                    coefficient_rows.append({"target_name":target,"fold_id":fold,"model_name":model_name,"feature":config.features[j],"intercept":float(model.intercept_.reshape(-1)[0]),
                      "standardized_coefficient":float(coef[j]),"raw_scale_coefficient":float(coef[j]/pre.scales[j]),"sign":int(np.sign(coef[j])),"absolute_magnitude_rank":rank,"convergence_warnings":len(w)})
                if model_name.endswith("selected"):
                    losses=np.abs(yv-p) if kind=="regression" else -(yv*np.log(np.clip(p,1e-12,1))+(1-yv)*np.log(np.clip(1-p,1e-12,1)))
                    bootstrap[f"{target}:{fold}:{model_name}"]=date_block_interval(dates[va],losses,config.seed,config.bootstrap_replicates)
    def merge(parts):
        keys=parts[0].keys(); return pa.table({k:pa.array(list(chain.from_iterable(x[k] for x in parts))) for k in keys})
    return merge(predictions),pa.Table.from_pylist(coefficient_rows),{"metrics":metrics,"preprocessing":preprocessing,"selected_hyperparameters":selected,"convergence_warnings":warnings_out,"date_block_intervals":bootstrap}
