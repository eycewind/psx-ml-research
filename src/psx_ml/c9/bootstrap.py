import numpy as np
def moving_block_bootstrap(values,block_length=5,iterations=2000,seed=42):
    values=np.asarray(values,float); n=len(values)
    if not n: return {"estimate":None,"lower_95":None,"upper_95":None,"iterations":iterations,"block_length":block_length}
    starts=np.arange(max(1,n-block_length+1)); rng=np.random.default_rng(seed); samples=[]
    for _ in range(iterations):
        chunks=[]
        while sum(len(x) for x in chunks)<n:
            s=int(rng.choice(starts)); chunks.append(values[s:min(n,s+block_length)])
        samples.append(float(np.mean(np.concatenate(chunks)[:n])))
    return {"estimate":float(np.mean(values)),"lower_95":float(np.quantile(samples,.025)),"upper_95":float(np.quantile(samples,.975)),"iterations":iterations,"block_length":block_length}
def empirical_p_value(observed,random_values):
    r=np.asarray(random_values,float); return float((1+np.sum(r>=observed))/(len(r)+1))
