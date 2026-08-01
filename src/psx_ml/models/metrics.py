from __future__ import annotations
import numpy as np
from scipy.stats import pearsonr,spearmanr
from sklearn.metrics import (average_precision_score,brier_score_loss,confusion_matrix,
 f1_score,log_loss,mean_absolute_error,mean_squared_error,precision_score,r2_score,recall_score,roc_auc_score)

def regression_metrics(y,p):
    y=np.asarray(y); p=np.asarray(p); n=len(y)
    pear=float(pearsonr(y,p).statistic) if n>1 and np.std(y)>1e-14 and np.std(p)>1e-14 else None
    spear=float(spearmanr(y,p).statistic) if n>1 and np.std(y)>1e-14 and np.std(p)>1e-14 else None
    return {"n":n,"mae":float(mean_absolute_error(y,p)),"rmse":float(mean_squared_error(y,p)**0.5),"r2":float(r2_score(y,p)),
      "pearson":pear,"spearman":spear,"directional_accuracy":float(np.mean((y>0)==(p>0)))}

def classification_metrics(y,prob):
    y=np.asarray(y,dtype=int); prob=np.clip(np.asarray(prob,dtype=float),1e-12,1-1e-12); pred=(prob>=.5).astype(int)
    bins=[]
    for lo in np.linspace(0,1,10,endpoint=False):
        mask=(prob>=lo)&(prob<(lo+.1) if lo<.9 else prob<=1)
        bins.append({"lower":float(lo),"upper":float(lo+.1),"n":int(mask.sum()),"mean_probability":float(prob[mask].mean()) if mask.any() else None,"observed_rate":float(y[mask].mean()) if mask.any() else None})
    auc=lambda fn: float(fn(y,prob)) if len(np.unique(y))==2 else None
    cm=confusion_matrix(y,pred,labels=[0,1]); tnr=cm[0,0]/cm[0].sum() if cm[0].sum() else 0.0; tpr=cm[1,1]/cm[1].sum() if cm[1].sum() else 0.0
    return {"n":len(y),"log_loss":float(log_loss(y,prob,labels=[0,1])),"brier":float(brier_score_loss(y,prob)),"roc_auc":auc(roc_auc_score),
      "pr_auc":auc(average_precision_score),"balanced_accuracy":float((tnr+tpr)/2),"precision":float(precision_score(y,pred,zero_division=0)),
      "recall":float(recall_score(y,pred,zero_division=0)),"f1":float(f1_score(y,pred,zero_division=0)),"confusion_matrix":cm.tolist(),
      "calibration_bins":bins,"prevalence":float(y.mean())}

def date_block_interval(dates,losses,seed=42,reps=200):
    dates=np.asarray(dates,dtype=object); losses=np.asarray(losses,dtype=float); unique=np.array(sorted(set(dates)),dtype=object)
    daily=np.array([losses[dates==d].mean() for d in unique]); rng=np.random.default_rng(seed)
    samples=np.array([daily[rng.integers(0,len(daily),len(daily))].mean() for _ in range(reps)])
    return {"estimate":float(daily.mean()),"lower_95":float(np.percentile(samples,2.5)),"upper_95":float(np.percentile(samples,97.5)),"dates":len(unique),"replicates":reps}
