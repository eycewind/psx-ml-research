import numpy as np
def moving_block_bootstrap(values,block_length=5,iterations=2000,seed=42):
    values=np.asarray(values,float); n=len(values)
    if not n: return {"estimate":None,"lower_95":None,"upper_95":None,"iterations":iterations,"block_length":block_length}
    effective_block=min(block_length,n); start_count=max(1,n-effective_block+1); blocks=(n+effective_block-1)//effective_block; rng=np.random.default_rng(seed)
    starts=rng.integers(0,start_count,size=(iterations,blocks)); offsets=np.arange(effective_block)
    indices=(starts[:,:,None]+offsets).reshape(iterations,-1)[:,:n]; samples=np.mean(values[indices],axis=1)
    return {"estimate":float(np.mean(values)),"lower_95":float(np.quantile(samples,.025)),"upper_95":float(np.quantile(samples,.975)),"iterations":iterations,"block_length":block_length}
def empirical_p_value(observed,random_values):
    r=np.asarray(random_values,float); return float((1+np.sum(r>=observed))/(len(r)+1))
