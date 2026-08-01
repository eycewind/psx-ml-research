from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass
class TrainOnlyPreprocessor:
    medians:np.ndarray|None=None; means:np.ndarray|None=None; scales:np.ndarray|None=None
    all_missing:list[int]|None=None; constant:list[int]|None=None
    def fit(self,x):
        x=np.asarray(x,dtype=float); self.all_missing=np.flatnonzero(np.all(~np.isfinite(x),axis=0)).tolist()
        self.medians=np.zeros(x.shape[1])
        for j in range(x.shape[1]):
            v=x[np.isfinite(x[:,j]),j]; self.medians[j]=np.median(v) if len(v) else 0.0
        z=np.where(np.isfinite(x),x,self.medians); self.means=np.mean(z,axis=0); self.scales=np.std(z,axis=0)
        self.constant=np.flatnonzero(self.scales==0).tolist(); self.scales[self.scales==0]=1.0; return self
    def transform(self,x):
        if self.medians is None: raise RuntimeError("preprocessor not fitted")
        z=np.where(np.isfinite(x),x,self.medians); return (z-self.means)/self.scales
    def state(self,features): return {"features":list(features),"medians":self.medians.tolist(),"means":self.means.tolist(),"scales":self.scales.tolist(),"all_missing":[features[i] for i in self.all_missing],"constant":[features[i] for i in self.constant]}
