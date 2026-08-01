from __future__ import annotations
import warnings
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression,Ridge
from threadpoolctl import threadpool_limits

def fit_ridge(x,y,alpha):
    with threadpool_limits(limits=1): return Ridge(alpha=alpha,fit_intercept=True,solver="cholesky").fit(x,y),[]

def fit_logistic(x,y,c,max_iter,seed):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always",ConvergenceWarning)
        with threadpool_limits(limits=1): model=LogisticRegression(C=c,penalty="l2",solver="lbfgs",max_iter=max_iter,random_state=seed,n_jobs=1).fit(x,y)
    return model,[str(w.message) for w in caught if issubclass(w.category,ConvergenceWarning)]
