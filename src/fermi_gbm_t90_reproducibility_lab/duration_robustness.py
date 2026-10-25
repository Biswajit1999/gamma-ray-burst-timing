"""Independent bin-edge, background and counting-noise T90 diagnostics.

Only conditional, binned Poisson statistics are treated. No new Fermi
observations, detector calibration, or correlated background model is implied.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class InterpolatedDuration:
    t5: float
    t95: float
    t90: float
    positive_excess_counts: float

@dataclass(frozen=True)
class WindowSensitivity:
    buffer_s: float
    background_model: str
    t90_s: float
    baseline_counts_in_signal: float

@dataclass(frozen=True)
class PoissonDurationUncertainty:
    point_t90_s: float
    low_s: float
    high_s: float
    successful_draws: int
    failed_draws: int
    n_draws: int

def _validate(edges, counts):
    edges=np.asarray(edges,dtype=float)
    counts=np.asarray(counts,dtype=float)
    if (edges.ndim!=1 or counts.ndim!=1 or len(edges)!=len(counts)+1
        or len(counts)<3 or not np.all(np.isfinite(edges))
        or not np.all(np.isfinite(counts)) or not np.all(np.diff(edges)>0)):
        raise ValueError('finite strictly increasing edges and matching counts required')
    return edges,counts

def interpolated_t90(edges, net_counts, signal_window=None):
    """5% and 95% cumulative-excess times, interpolated within each bin.

    Negative residual bins are clipped; this can bias low-SNR T90 upward.
    Only bins fully contained within a supplied signal window are used.
    """
    edges,counts=_validate(edges,net_counts)
    if signal_window is not None:
        lo,hi=map(float,signal_window)
        if not np.all(np.isfinite([lo,hi])) or lo>=hi:
            raise ValueError('invalid signal window')
        indices=np.flatnonzero((edges[:-1]>=lo)&(edges[1:]<=hi))
        if not len(indices) or not np.all(np.diff(indices)==1):
            raise ValueError('no contiguous complete bins in signal window')
        counts=counts[indices]
        edges=edges[indices[0]:indices[-1]+2]
    counts=np.maximum(counts,0.)
    total=float(np.sum(counts))
    if total<=0:
        raise ValueError('no positive excess')
    cumulative=np.cumsum(counts)
    def percentile(q):
        target=q*total
        i=min(int(np.searchsorted(cumulative,target,side='left')),len(counts)-1)
        previous=float(cumulative[i-1]) if i else 0.
        return float(edges[i]+(target-previous)/counts[i]*(edges[i+1]-edges[i]))
    t5,t95=percentile(.05),percentile(.95)
    return InterpolatedDuration(t5,t95,t95-t5,total)

def _background(edges,counts,window,model,buffer_s):
    if model not in ('constant','linear'):
        raise ValueError('unknown background model')
    if not np.isfinite(buffer_s) or buffer_s<0:
        raise ValueError('invalid exclusion buffer')
    lo,hi=map(float,window)
    if not np.all(np.isfinite([lo,hi])) or lo>=hi:
        raise ValueError('invalid signal window')
    width=np.diff(edges)
    centres=(edges[:-1]+edges[1:])/2
    outside=(edges[1:]<=lo-buffer_s)|(edges[:-1]>=hi+buffer_s)
    ncoef=1 if model=='constant' else 2
    if np.count_nonzero(outside)<=ncoef:
        raise ValueError('insufficient off-burst bins')
    x=centres-np.mean(centres[outside])
    matrix=np.ones((len(centres),ncoef))
    if ncoef==2:
        matrix[:,1]=x
    # Width-weighted regression on count rates: an approximation to
    # inverse-variance weighting for near-constant Poisson background rate.
    w=np.sqrt(width[outside])
    weighted=matrix[outside]*w[:,None]
    if np.linalg.matrix_rank(weighted)<ncoef:
        raise ValueError('degenerate background design')
    coef=np.linalg.lstsq(weighted,counts[outside]/width[outside]*w,rcond=None)[0]
    return np.maximum(matrix@coef,0.)*width

def fitted_duration(edges,observed_counts,signal_window,model='constant',buffer_s=0.):
    """Fit off-burst background rate and calculate conditional window T90."""
    edges,counts=_validate(edges,observed_counts)
    if np.any(counts<0):
        raise ValueError('Poisson counts must be nonnegative')
    background=_background(edges,counts,signal_window,model,buffer_s)
    mask=(edges[:-1]>=signal_window[0])&(edges[1:]<=signal_window[1])
    return interpolated_t90(edges,counts-background,signal_window),float(np.sum(background[mask]))

def background_window_sensitivity(edges,observed_counts,signal_window,
                                  buffers_s=(0.,2.,5.),models=('constant','linear')):
    """Recompute T90 over declared background masks and model choices."""
    results=[]
    for buffer in buffers_s:
        for model in models:
            d,baseline=fitted_duration(edges,observed_counts,signal_window,model,buffer)
            results.append(WindowSensitivity(float(buffer),model,d.t90,baseline))
    return results

def poisson_duration_uncertainty(edges,observed_counts,signal_window,model='constant',
                                 buffer_s=0.,n_draws=300,confidence=.95,seed=20261025):
    """Conditional Poisson plug-in resampling, with background refit per draw.

    No background calibration covariance or astrophysical source prior is
    included. The fraction of failed fits is reported, not silently dropped.
    """
    edges,counts=_validate(edges,observed_counts)
    if np.any(counts<0):
        raise ValueError('Poisson counts must be nonnegative')
    if not isinstance(n_draws,int) or n_draws<20 or not 0<confidence<1:
        raise ValueError('n_draws>=20 and 0<confidence<1 required')
    point,_=fitted_duration(edges,counts,signal_window,model,buffer_s)
    rng=np.random.default_rng(seed)
    samples=[]
    for _ in range(n_draws):
        draw=rng.poisson(counts)
        try:
            estimate,_=fitted_duration(edges,draw,signal_window,model,buffer_s)
            samples.append(estimate.t90)
        except ValueError:
            pass
    if len(samples)<max(20,int(.8*n_draws)):
        raise ValueError('too few successful resamples')
    alpha=(1-confidence)/2
    return PoissonDurationUncertainty(point.t90,float(np.quantile(samples,alpha)),
        float(np.quantile(samples,1-alpha)),len(samples),n_draws-len(samples),n_draws)
