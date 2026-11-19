"""Reproducible *synthetic* GBM-like duration injection and uncertainty test."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from fermi_gbm_t90_reproducibility_lab.duration_robustness import (
    fitted_duration, background_window_sensitivity, poisson_duration_uncertainty,
)

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path)
    parser.add_argument('--seed',type=int,default=20261025)
    args=parser.parse_args()
    edges=np.arange(-20.,41.,1.)
    centres=(edges[:-1]+edges[1:])/2
    baseline=50.+.2*centres
    burst=np.where((centres>=0)&(centres<8),300.,0.)
    rng=np.random.default_rng(args.seed)
    observed=rng.poisson(baseline+burst)
    signal_window=(0.,8.)
    fitted,_=fitted_duration(edges,observed,signal_window,model='linear')
    sensitivity=background_window_sensitivity(edges,observed,signal_window)
    bootstrap=poisson_duration_uncertainty(edges,observed,signal_window,
        model='linear',n_draws=300,seed=args.seed)
    report={
        'data_type':'seeded synthetic binned Poisson counts; not Fermi observational data',
        'seed':args.seed,'bin_width_s':1.,'background_rate_counts_per_s':'50+0.2*t',
        'injected_rectangular_excess_counts_per_s':300.,
        'injected_full_pulse_duration_s':8.,
        'theoretical_t90_s':7.2,
        'measured_t90_s':fitted.t90,
        'model_window_sensitivity':[
            {'buffer_s':x.buffer_s,'model':x.background_model,
             't90_s':x.t90_s,'background_counts_in_signal':x.baseline_counts_in_signal}
            for x in sensitivity],
        'conditional_poisson_interval':{
            'point_s':bootstrap.point_t90_s,'low_s':bootstrap.low_s,
            'high_s':bootstrap.high_s,'successful_draws':bootstrap.successful_draws,
            'failed_draws':bootstrap.failed_draws},
        'limitations':'Plug-in Poisson resampling; no response calibration or correlated background systematics.'
    }
    text=json.dumps(report,indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text+'\n',encoding='utf-8')
    print(text)

if __name__=='__main__':
    main()
