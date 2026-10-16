import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from sector_pairs.config import Config
from sector_pairs.strategy import run_strategy
from experiments.engine import simulate
from experiments.run import rolling_threshold

MODEL={'pair':'Y/X','y':'Y','x':'X','alpha':0.,'beta':1.,'sigma':.1,'mu':0.}

def prices(s):
    idx=pd.bdate_range('2020-01-01',periods=len(s));x=np.exp(4+np.arange(len(s))*.0002)
    return pd.DataFrame({'X':x,'Y':x*np.exp(s)},index=idx)

def test_new_engine_control_matches_original_simple_returns_and_leg_costs():
    p=prices([-.2,-.3,-.01,.2,.3,.01,-.3,-.4])
    old=run_strategy(p,MODEL,Config(),executable_costs=True)
    new=simulate(p,MODEL,Config(),'static',0,0)
    columns=['position','target','entry','exit','gross','cost','net','turnover','exposure']
    assert_frame_equal(old[columns],new[columns])

def test_timeout_requires_an_observed_reset_before_reentry():
    p=prices([-.2,-.3,-.4,-.3,-.2,-.01,-.2,-.1])
    f=simulate(p,MODEL,Config(),'static',0,0,max_holding=2,reset_after_timeout=True)
    assert f.position.tolist()==[1,1,0,0,0,0,1,1]
    assert f.timeout.sum()==1 and f.entry.sum()==2
    assert f.cost.iloc[2]>0

def test_threshold_excludes_current_observation():
    x=pd.Series(np.arange(400,dtype=float))
    before=rolling_threshold(x)
    changed=x.copy();changed.iloc[300]=1e9
    after=rolling_threshold(changed)
    assert before.iloc[300]==after.iloc[300]
    assert before.iloc[:301].equals(after.iloc[:301])

def test_future_prices_cannot_change_timeout_or_local_filter_history():
    rng=np.random.default_rng(6);s=np.cumsum(rng.normal(0,.02,400))
    p=prices(s);changed=p.copy();changed.iloc[300:,changed.columns.get_loc('Y')]*=3
    high=pd.Series(np.arange(len(p))%7==0,index=p.index)
    a=simulate(p,MODEL,Config(),'static',0,100,high=high,action='entry_filter',max_holding=60,reset_after_timeout=True)
    b=simulate(changed,MODEL,Config(),'static',0,100,high=high,action='entry_filter',max_holding=60,reset_after_timeout=True)
    assert_frame_equal(a.iloc[:300],b.iloc[:300])
