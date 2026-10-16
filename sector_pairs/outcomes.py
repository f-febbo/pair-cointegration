"""Labels only: future observations never used to construct trading features."""
import numpy as np
import pandas as pd

def forward_outcomes(prices, model, config, frame, horizon):
    idx=prices.index; s=frame.spread.to_numpy(); m=frame['mean'].to_numpy()
    z=frame.z.to_numpy(); n=len(idx); h=horizon; sigma=model['sigma']
    leg=(prices[model['y']].pct_change(fill_method=None)-model['beta']*prices[model['x']].pct_change(fill_method=None))/(1+abs(model['beta']))
    returns=leg.to_numpy()
    rows=[]
    for i in range(n-h):
        if not np.isfinite(m[i]):
            continue
        initial=s[i]-m[i]; a=abs(initial); direction=-np.sign(initial)
        future=s[i+1:i+h+1]
        small=a < .05*sigma
        distances=np.abs(future-m[i])
        hit=np.flatnonzero(distances<=config.exit*sigma)
        # Hypothetical current-direction entry, or continuation of an existing position.
        future_z=z[i+1:i+h+1]
        exit_hits=np.flatnonzero(np.abs(future_z)<=config.exit)
        duration=int(exit_hits[0]+1) if len(exit_hits) else h
        hypothetical=direction*returns[i+1:i+duration+1]
        hypothetical=hypothetical.copy()
        hypothetical[-1]-=config.cost # explicit horizon mark-out liquidation if not exited
        trade_return=(1-config.cost)*np.prod(1+hypothetical)-1 if not small else np.nan
        existing=frame.position.iloc[i]!=0 and not frame.entry.iloc[i]
        continuation=np.nan
        if existing:
            held=frame.position.iloc[i]*returns[i+1:i+duration+1].copy()
            held[-1]-=config.cost
            continuation=np.prod(1+held)-1
        x=future[:-1]; y=future[1:]
        phi=np.sum((x-x.mean())*(y-y.mean()))/np.sum((x-x.mean())**2) if np.var(x)>1e-14 else np.nan
        rows.append({'date':idx[i],'label_end':idx[i+h], 'horizon':h,
                     'convergence':np.nan if small else 1-distances[-1]/a,
                     'converged':np.nan if small else float(bool(len(hit))),
                     'convergence_time_capped':np.nan if small else (int(hit[0]+1) if len(hit) else h+1),
                     'adverse_excursion':np.nan if small else max(0.,float(np.max(-direction*(future-s[i])/sigma))),
                     'trade_return':trade_return, 'adverse_trade':np.nan if small else float(trade_return<0),
                     'existing_return':continuation, 'entry_opportunity':bool(frame.entry.iloc[i]),
                     'existing_position':existing, 'near_zero_deviation':small,
                     'future_phi':phi, 'future_phi_observations':h-1,
                     'censored_trade':not bool(len(exit_hits)), 'hit_by_horizon':bool(len(hit))})
    return pd.DataFrame(rows).set_index('date')

def purge_labels(panel, bounds):
    """Assign features to a stage only if their complete label stays inside it."""
    panel=panel.copy(); panel['stage']='purged'
    dates=pd.to_datetime(panel['date']); ends=pd.to_datetime(panel['label_end'])
    for stage in ('development','validation','test'):
        b=bounds[stage]
        mask=(dates>=pd.Timestamp(b['start'])) & (dates<=pd.Timestamp(b['end'])) & (ends<=pd.Timestamp(b['end']))
        panel.loc[mask,'stage']=stage
    return panel
