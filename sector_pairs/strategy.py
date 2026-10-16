"""Close-t decisions earn close-t to close-(t+1) returns.

Reference costs are 5bp per scalar spread-position change. The executable
diagnostic also charges turnover needed to restore constant dollar leg weights.
"""
import numpy as np
import pandas as pd
from .cointegration import spread

def signals(prices, model, config, mean_kind):
    s=spread(prices,model)
    if mean_kind=='static':
        mean=pd.Series(model['mu'],index=s.index)
    elif mean_kind=='calendar3y':
        indexer=pd.api.indexers.VariableOffsetWindowIndexer(index=s.index,offset=pd.DateOffset(years=3))
        mean=s.rolling(indexer,min_periods=500,closed='right').mean()
    else:
        mean=s.rolling(config.rolling_mean_days, min_periods=config.rolling_mean_days).mean()
    return pd.DataFrame({'spread':s,'mean':mean,'z':(s-mean)/model['sigma']})

def run_strategy(prices, model, config, mean_kind='static', start=0,
                 high=None, modification='control', executable_costs=False,
                 return_convention='simple'):
    sig=signals(prices,model,config,mean_kind)
    idx=prices.index
    high=pd.Series(False,index=idx) if high is None else high.reindex(idx).fillna(False)
    position=np.zeros(len(idx)); targets=np.zeros(len(idx)); entries=np.zeros(len(idx),bool)
    suppressed=np.zeros(len(idx),bool); exits=np.zeros(len(idx),bool)
    state=0
    for i in range(start,len(idx)):
        z=sig.z.iloc[i]
        if not np.isfinite(z):
            position[i]=state; targets[i]=state
            continue
        if state and abs(z)<=config.exit:
            state=0; exits[i]=True
        elif not state and abs(z)>=config.entry and i<len(idx)-1:
            if modification=='entry_filter' and high.iloc[i]:
                suppressed[i]=True
            else:
                state=-np.sign(z); entries[i]=True
        position[i]=state
        targets[i]=state*(config.reduced_exposure if modification=='reduction' and high.iloc[i] else 1.)
    target=pd.Series(targets,index=idx)
    beta=model['beta']; denom=1+abs(beta)
    weights=pd.DataFrame({'y':target/denom, 'x':-target*beta/denom})
    returns=prices[[model['y'],model['x']]].pct_change(fill_method=None).fillna(0)
    returns.columns=['y','x']
    held=weights.shift(1).fillna(0)
    simple_gross=(held*returns).sum(axis=1)
    if return_convention=='reference_log':
        gross=target.shift(1).fillna(0)*sig.spread.diff().fillna(0)/denom
    elif return_convention=='simple':
        gross=simple_gross
    else:
        raise ValueError('Unknown return convention')
    # Portfolio dollar weights after today's asset returns, before rebalancing.
    drift=held.mul(1+returns).div(1+simple_gross,axis=0)
    leg_turnover=(weights-drift).abs().sum(axis=1)
    scalar_turnover=target.diff().abs().fillna(target.abs())
    turnover=leg_turnover if executable_costs else scalar_turnover
    cost=config.cost*turnover
    out=sig.assign(position=position,target=target,entry=entries,exit=exits,suppressed=suppressed,
                   high=high,gross=gross,cost=cost,net=gross-cost,
                   exposure=held.abs().sum(axis=1),turnover=turnover,leg_turnover=leg_turnover)
    out.iloc[:start, out.columns.get_indexer(['gross','cost','net','exposure','turnover'])]=0
    return out

def trade_ledger(frame):
    records=[]; active=None
    for date,row in frame.iterrows():
        if active is not None:
            active['wealth']*=1+row.net
            active['days']+=1
        if row['exit'] and active is not None:
            active.update(exit_date=date,completed=True,net_return=active.pop('wealth')-1)
            records.append(active); active=None
        if row.entry:
            active=dict(entry_date=date,exit_date=pd.NaT,direction=row.position,
                        wealth=1-row.cost,days=0,completed=False)
    if active is not None:
        active['net_return']=active.pop('wealth')-1
        records.append(active)
    return pd.DataFrame(records,columns=['entry_date','exit_date','direction','days','completed','net_return'])
