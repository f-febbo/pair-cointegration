"""Close-aligned state machine for separately declared strategy experiments."""
import numpy as np
import pandas as pd
from sector_pairs.strategy import signals

def simulate(prices,model,config,mean_kind,start,deployment,high=None,action='control',
             alternative_z=None,max_holding=None,reset_after_timeout=False,cost_multiplier=1.):
    original=signals(prices,model,config,mean_kind)
    z=original.z.to_numpy().copy()
    if alternative_z is not None:
        z[deployment:]=alternative_z.reindex(prices.index).to_numpy()[deployment:]
    high=pd.Series(False,index=prices.index) if high is None else high.reindex(prices.index).fillna(False)
    n=len(prices);positions=np.zeros(n);targets=np.zeros(n)
    entries=np.zeros(n,bool);exits=np.zeros(n,bool);timeouts=np.zeros(n,bool);denied=np.zeros(n,bool)
    state=0.;age=0;armed=True
    for i in range(start,n):
        active=i>=deployment;v=z[i]
        if not np.isfinite(v):
            positions[i]=targets[i]=state
            continue
        if not armed and abs(v)<=config.exit:
            armed=True
        if state:
            age+=1
            timeout=active and max_holding is not None and age>=max_holding
            if abs(v)<=config.exit or timeout:
                state=0;exits[i]=True;timeouts[i]=timeout
                if timeout and reset_after_timeout:
                    armed=False
        elif abs(v)>=config.entry and i<n-1:
            if not armed or (active and action=='entry_filter' and high.iloc[i]):
                denied[i]=True
            else:
                state=-np.sign(v);age=0;entries[i]=True
        positions[i]=state
        targets[i]=state*(config.reduced_exposure if active and action=='reduction' and high.iloc[i] else 1.)
    q=pd.Series(targets,index=prices.index)
    denom=1+abs(model['beta'])
    weights=pd.DataFrame({'y':q/denom,'x':-q*model['beta']/denom})
    r=prices[[model['y'],model['x']]].pct_change(fill_method=None).fillna(0)
    r.columns=['y','x']
    held=weights.shift(1).fillna(0)
    gross=(held*r).sum(axis=1)
    drift=held.mul(1+r).div(1+gross,axis=0)
    turnover=(weights-drift).abs().sum(axis=1)
    cost=config.cost*cost_multiplier*turnover
    return original.assign(z=z,position=positions,target=targets,entry=entries,exit=exits,
                           timeout=timeouts,suppressed=denied,high=high,gross=gross,
                           net=gross-cost,cost=cost,turnover=turnover,exposure=held.abs().sum(axis=1))
