"""Conditional GRB T90 observation-window and background sensitivity diagnostics."""
import numpy as np

def quantile_duration(edges, excess, fractions=(0.05, 0.95)):
    edges = np.asarray(edges, dtype=float)
    excess = np.asarray(excess, dtype=float)
    if edges.ndim != 1 or excess.ndim != 1 or len(edges) != len(excess)+1 or len(excess) < 2:
        raise ValueError("edges must delimit at least two bins")
    if not np.all(np.isfinite(edges)) or not np.all(np.diff(edges)>0) or not np.all(np.isfinite(excess)) or np.any(excess < 0) or excess.sum() <= 0:
        raise ValueError("invalid bin edges or nonnegative excess counts")
    c = np.r_[0., np.cumsum(excess)]
    t = np.interp(np.asarray(fractions)*c[-1], c, edges)
    return float(t[0]), float(t[1]), float(t[1]-t[0])

def window_sweep(edges, excess, right_edges):
    """Conditional T90 from complete bins up to each supplied right boundary."""
    edges = np.asarray(edges, float)
    excess = np.asarray(excess, float)
    out = []
    for boundary in right_edges:
        k = int(np.searchsorted(edges, boundary, side="right")-1)
        if k < 2 or k > len(excess):
            raise ValueError("right boundary must retain >=2 complete bins")
        out.append((float(edges[k]), *quantile_duration(edges[:k+1], excess[:k])))
    return np.asarray(out)

def background_ensemble(edges, observed, backgrounds):
    """Background assumptions are externally supplied; negative excess is clipped."""
    observed = np.asarray(observed, float)
    backgrounds = np.asarray(backgrounds, float)
    if backgrounds.ndim != 2 or backgrounds.shape[1] != len(observed) or not np.all(np.isfinite(backgrounds)) or not np.all(np.isfinite(observed)) or np.any(backgrounds < 0) or np.any(observed < 0):
        raise ValueError("invalid count or background model")
    return np.array([quantile_duration(edges, np.maximum(observed-b, 0))[-1] for b in backgrounds])
