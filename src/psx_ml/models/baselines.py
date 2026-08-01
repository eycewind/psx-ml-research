import numpy as np

def regression_baselines(y_train,n): return {"zero_return_baseline":np.zeros(n),"training_mean_baseline":np.full(n,float(np.mean(y_train)))}
def classification_baselines(y_train,n):
    p=float(np.mean(y_train)); majority=float(p>0.5)
    return {"majority_class_baseline":np.full(n,majority),"training_prevalence_baseline":np.full(n,p)}
