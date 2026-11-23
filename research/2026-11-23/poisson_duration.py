"""Conditional low-count burst-duration diagnostics; no catalogue inference."""
import numpy as np

def on_off_net(on, off, alpha):
    """Net counts and independent Poisson variance for on/off exposure ratio alpha."""
    a = np.asarray(on, dtype=float)
    b = np.asarray(off, dtype=float)
    if a.shape != b.shape or a.ndim != 1 or a.size < 2:
        raise ValueError("matching one-dimensional bins required")
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)) or np.any(a < 0) or np.any(b < 0):
        raise ValueError("counts must be finite and nonnegative")
    if not np.isfinite(alpha) or alpha <= 0:
        raise ValueError("alpha must be positive and finite")
    return a - alpha*b, a + alpha**2*b

def t90_from_net(net, edges):
    """T90 using positive net counts and uniform-within-bin interpolation."""
    n = np.asarray(net, dtype=float)
    e = np.asarray(edges, dtype=float)
    if n.ndim != 1 or e.shape != (n.size+1,) or n.size < 2:
        raise ValueError("bin/edge shape mismatch")
    if not np.all(np.isfinite(n)) or not np.all(np.isfinite(e)) or np.any(np.diff(e) <= 0):
        raise ValueError("invalid values or time edges")
    weights = np.maximum(n, 0)
    if weights.sum() <= 0:
        raise ValueError("no positive net counts")
    cum = np.r_[0, np.cumsum(weights)]
    targets = weights.sum()*np.array([0.05, 0.95])
    positions = []
    for target in targets:
        i = min(np.searchsorted(cum, target, side="right")-1, n.size-1)
        positions.append(e[i] + (target-cum[i])/weights[i]*(e[i+1]-e[i]))
    return positions[1]-positions[0]

def poisson_t90_bootstrap(on, off, alpha, edges, draws=1000, seed=0):
    """Conditional plug-in Poisson resampling; excludes zero-signal realizations."""
    net, _ = on_off_net(on, off, alpha)
    if not isinstance(draws, int) or draws < 2:
        raise ValueError("draws must be >=2")
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(draws):
        a = rng.poisson(on)
        b = rng.poisson(off)
        try:
            estimates.append(t90_from_net(a-alpha*b, edges))
        except ValueError:
            pass
    if len(estimates) < 2:
        raise ValueError("insufficient valid bootstrap realizations")
    return np.quantile(estimates, [0.025, 0.5, 0.975]), len(estimates)/draws
