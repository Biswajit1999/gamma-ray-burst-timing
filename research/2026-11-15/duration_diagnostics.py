"""Synthetic binned GRB duration diagnostics; not a catalogue estimator."""
import numpy as np

def interpolated_duration(edges, net_counts, fractions=(0.05, 0.95)):
    """Crossings of clipped cumulative counts, linear within each bin."""
    edges=np.asarray(edges,dtype=float)
    counts=np.asarray(net_counts,dtype=float)
    q=np.asarray(fractions,dtype=float)
    if edges.ndim!=1 or counts.ndim!=1 or len(edges)!=len(counts)+1 or not len(counts):
        raise ValueError("one more edge than counts required")
    if not np.all(np.isfinite(edges)) or not np.all(np.diff(edges)>0) or not np.all(np.isfinite(counts)):
        raise ValueError("finite increasing edges and counts required")
    if q.shape!=(2,) or not (0<q[0]<q[1]<1):
        raise ValueError("invalid fractions")
    positive=np.maximum(counts,0)
    total=positive.sum()
    if not np.isfinite(total) or total<=0:
        raise ValueError("positive excess required")
    cumulative=np.r_[0.,np.cumsum(positive)]
    times=[]
    for f in q:
        target=f*total
        i=min(int(np.searchsorted(cumulative,target,side="right")-1),len(counts)-1)
        while i<len(counts)-1 and positive[i]==0:
            i+=1
        times.append(edges[i]+(target-cumulative[i])/positive[i]*(edges[i+1]-edges[i]))
    return float(times[0]),float(times[1]),float(times[1]-times[0])

def background_ensemble(edges,observed_counts,background_models):
    """Return duration per assumed background and its range, not a confidence interval."""
    observed=np.asarray(observed_counts,dtype=float)
    models=np.asarray(background_models,dtype=float)
    if models.ndim!=2 or models.shape[1:]!=observed.shape or models.shape[0]<1:
        raise ValueError("expected (model,bin) background array")
    if not np.all(np.isfinite(models)) or np.any(models<0) or not np.all(np.isfinite(observed)):
        raise ValueError("finite counts and nonnegative background required")
    durations=np.array([interpolated_duration(edges,observed-b)[2] for b in models])
    return durations,float(np.ptp(durations))
