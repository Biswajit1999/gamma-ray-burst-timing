"""Generate a synthetic sensitivity plot; no observational data."""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from duration_diagnostics import background_ensemble

def main(output="figures/fig06_synthetic_background_sensitivity.png"):
    edges=np.linspace(-5,15,81)
    center=(edges[:-1]+edges[1:])/2
    observed=90*np.exp(-.5*((center-4)/1.4)**2)+12
    levels=np.arange(10.,15.)
    models=np.array([np.full(len(center),v) for v in levels])
    durations,spread=background_ensemble(edges,observed,models)
    fig,ax=plt.subplots()
    ax.plot(levels,durations,"o-")
    ax.set(xlabel="Assumed background counts per bin",ylabel="Interpolated T90 [s]",title=f"Synthetic sensitivity; range {spread:.3f} s")
    fig.tight_layout()
    path=Path(output)
    path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path,dpi=150)
    plt.close(fig)
    return path

if __name__=="__main__":
    main()
