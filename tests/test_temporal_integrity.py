"""Synthetic fixtures test alignment; they never supply reported research results."""
from dataclasses import replace
import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from sector_pairs.config import Config
from sector_pairs.strategy import run_strategy, trade_ledger
from sector_pairs.diagnostics import indicators, half_life
from sector_pairs.outcomes import forward_outcomes, purge_labels
from sector_pairs.performance import metrics

MODEL={'pair':'Y/X','y':'Y','x':'X','alpha':0.,'beta':1.,'mu':0.,'sigma':.1}

def prices(spreads):
    idx=pd.bdate_range('2015-01-01',periods=len(spreads))
    x=np.exp(4+np.arange(len(spreads))*.0002)
    return pd.DataFrame({'X':x,'Y':x*np.exp(spreads)},index=idx)

def test_close_signal_earns_next_day_and_exit_cost_is_charged():
    p=prices([-.20,-.25,-.02,-.20])
    f=run_strategy(p,MODEL,Config())
    assert f.position.tolist()==[1,1,0,0]
    assert f.gross.iloc[0]==0
    expected=(p.Y.pct_change()-p.X.pct_change())/2
    assert f.gross.iloc[1]==pytest.approx(expected.iloc[1])
    assert f.gross.iloc[2]==pytest.approx(expected.iloc[2])
    assert f.cost.tolist()==[.0005,0,.0005,0]
    assert f.gross.iloc[3]==0
    ledger=trade_ledger(f)
    assert len(ledger)==1 and ledger.completed.iloc[0]
    assert ledger.net_return.iloc[0]==pytest.approx((1+f.net).prod()-1)

def test_entry_filter_preserves_existing_position_and_original_exit():
    p=prices([-.2,-.3,-.2,-.01,-.2,-.25,-.01])
    high=pd.Series([False,True,True,True,True,True,True],index=p.index)
    f=run_strategy(p,MODEL,Config(),high=high,modification='entry_filter')
    assert f.position.tolist()==[1,1,1,0,0,0,0]
    assert f.suppressed.sum()==2
    assert f.exit.iloc[3]

def test_reduction_rebalances_and_pays_cost_in_both_directions():
    p=prices([-.2,-.3,-.2,-.01,-.2])
    high=pd.Series([False,True,False,False,False],index=p.index)
    f=run_strategy(p,MODEL,Config(),high=high,modification='reduction')
    assert f.target.tolist()==[1,.5,1,0,0]
    assert f.cost.tolist()==[.0005,.00025,.00025,.0005,0]
    assert f.exposure.iloc[2]==.5

def test_strategy_and_diagnostics_do_not_change_when_future_prices_change():
    rng=np.random.default_rng(41)
    s=np.zeros(1500)
    for i in range(1,len(s)):s[i]=.98*s[i-1]+rng.normal(0,.008)
    p=prices(s);cut=1200
    revised=p.copy();revised.iloc[cut:,revised.columns.get_loc('Y')]*=3
    cfg=Config()
    a=run_strategy(p,MODEL,cfg,'rolling',start=760)
    b=run_strategy(revised,MODEL,cfg,'rolling',start=760)
    assert_frame_equal(a.iloc[:cut],b.iloc[:cut])
    da=indicators(p,MODEL,cfg,a);db=indicators(revised,MODEL,cfg,b)
    assert_frame_equal(da.iloc[:cut],db.iloc[:cut])

def test_forward_labels_use_t_plus_one_through_horizon_only():
    p=prices([-.20,-.15,-.10,-.08,-.06,-.04,-.01,-.05])
    cfg=Config(horizons=(5,));f=run_strategy(p,MODEL,cfg)
    out=forward_outcomes(p,MODEL,cfg,f,5)
    row=out.iloc[0]
    assert row.convergence==pytest.approx(.8)
    assert row.converged==0
    assert row.future_phi_observations==4
    assert row.label_end==p.index[5]
    assert out.index[-1]==p.index[2]
    changed=p.copy();changed.iloc[6:,changed.columns.get_loc('Y')]*=5
    f2=run_strategy(changed,MODEL,cfg)
    out2=forward_outcomes(changed,MODEL,cfg,f2,5)
    pd.testing.assert_series_equal(row,out2.iloc[0])

def test_rolling_outcome_equilibrium_stays_frozen_at_t():
    p=prices([-.2,-.3,-.4,-.25,-.1,.1,.2,.1])
    cfg=replace(Config(),rolling_mean_days=3)
    f=run_strategy(p,MODEL,cfg,'rolling')
    o=forward_outcomes(p,MODEL,cfg,f,3)
    t=p.index[3]
    expected=1-abs(f.spread.iloc[6]-f['mean'].loc[t])/abs(f.spread.loc[t]-f['mean'].loc[t])
    assert o.loc[t,'convergence']==pytest.approx(expected)

def test_near_zero_deviation_excluded_and_half_life_validity():
    p=prices([0,.1,.05,.02,.01,.005,.004])
    f=run_strategy(p,MODEL,Config())
    o=forward_outcomes(p,MODEL,Config(),f,5)
    assert o.near_zero_deviation.iloc[0]
    assert np.isnan(o.convergence.iloc[0])
    values=half_life(pd.Series([-1,0,.5,1,1.1]))
    assert values.iloc[2]==pytest.approx(1)
    assert values.drop(index=2).isna().all()

def test_labels_crossing_validation_or_test_boundary_are_purged():
    p=pd.DataFrame({'date':pd.to_datetime(['2020-01-02','2020-01-09','2020-01-12']),
                    'label_end':pd.to_datetime(['2020-01-06','2020-01-13','2020-01-17'])})
    bounds={'development':{'start':'2020-01-01','end':'2020-01-10'},
            'validation':{'start':'2020-01-11','end':'2020-01-20'},
            'test':{'start':'2020-01-21','end':'2020-01-30'}}
    assert purge_labels(p,bounds).stage.tolist()==['development','purged','validation']

def test_drawdown_includes_initial_capital():
    f=pd.DataFrame({'net':[-.1,.02]})
    assert metrics(f)['max_drawdown']==pytest.approx(-.1)

def test_gross_leg_exposure_uses_absolute_negative_beta():
    p=prices([-.2,-.3,-.1,-.01])
    m=dict(MODEL,beta=-.5,alpha=6)
    f=run_strategy(p,m,Config())
    assert f.exposure.max()<=1+1e-12

def test_reference_log_approximation_is_separate_from_investable_leg_return():
    p=prices([-.2,-.3,-.1,-.01])
    simple=run_strategy(p,MODEL,Config())
    ref=run_strategy(p,MODEL,Config(),return_convention='reference_log')
    expected=simple.position.shift(1).fillna(0)*simple.spread.diff().fillna(0)/2
    np.testing.assert_allclose(ref.gross,expected)
    assert not np.allclose(simple.gross,ref.gross)
    np.testing.assert_array_equal(simple.position,ref.position)

def test_hypothetical_entry_cost_is_paid_at_feature_close():
    p=prices([-.2,-.3,-.15,-.1,-.05,-.04,-.03])
    cfg=Config();f=run_strategy(p,MODEL,cfg)
    o=forward_outcomes(p,MODEL,cfg,f,5)
    leg=(p.Y.pct_change()-p.X.pct_change())/2
    held=leg.iloc[1:6].copy();held.iloc[-1]-=cfg.cost
    assert o.trade_return.iloc[0]==pytest.approx((1-cfg.cost)*(1+held).prod()-1)

def test_existing_continuation_respects_actual_direction_after_zero_crossing():
    p=prices([-.2,-.1,.05,.15,.2,.25,.3,.35])
    f=run_strategy(p,MODEL,Config())
    assert f.position.iloc[2]==1 and f.z.iloc[2]>0
    o=forward_outcomes(p,MODEL,Config(),f,5)
    # Existing long remains long despite current positive deviation.
    assert o.loc[p.index[2],'existing_position']
    assert o.loc[p.index[2],'existing_return']>0
    assert o.loc[p.index[2],'trade_return']<0
