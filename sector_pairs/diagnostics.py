"""Trailing local estimates; standard errors and CUSUM are descriptive only."""
import numpy as np
import pandas as pd
from .cointegration import spread

def rolling_ols(y, x, window):
    mx=x.rolling(window).mean(); my=y.rolling(window).mean()
    vx=x.rolling(window).var(ddof=1); vy=y.rolling(window).var(ddof=1)
    cov=y.rolling(window).cov(x)
    beta=cov/vx.where(vx>1e-14)
    alpha=my-beta*mx
    sse=((window-1)*(vy-beta*cov)).clip(lower=0)
    dispersion=np.sqrt(sse/(window-2))
    se=dispersion/np.sqrt((window-1)*vx)
    return pd.DataFrame({'alpha':alpha,'beta':beta,'residual_vol':dispersion,'beta_se':se})

def half_life(phi):
    return np.log(.5)/np.log(phi.where((phi>0)&(phi<1)))

def indicators(prices, model, config, sig):
    s=spread(prices,model)
    out=pd.DataFrame(index=s.index)
    out['abs_z']=sig.z.abs()
    out['recent_vol']=s.diff().rolling(20).std()
    out['recent_spread_return']=(s-s.shift(20))/model['sigma']
    # A trailing rate of *matured* 20-day entry-sized deviations reaching .25 sigma.
    old_z=sig.z.shift(20)
    touched=pd.concat([((s.shift(k)-sig['mean'].shift(20)).abs()<=.25*model['sigma']) for k in range(20)],axis=1).any(axis=1)
    eligible=old_z.abs()>=config.entry
    matured=touched.astype(float).where(eligible)
    out['trailing_convergence']=matured.rolling(126,min_periods=5).mean()
    out['matured_opportunities']=eligible.rolling(126).sum()
    out['cusum_descriptive']=(s-model['mu']).rolling(63).sum()/(model['sigma']*np.sqrt(63))
    for w in config.windows:
        ols=rolling_ols(np.log(prices[model['y']]),np.log(prices[model['x']]),w)
        ar=rolling_ols(s,s.shift(1),w)
        phi=ar.beta
        history_sd=ols.beta.shift(1).rolling(w).std()
        adaptive_residual=np.log(prices[model['y']])-ols.alpha-ols.beta*np.log(prices[model['x']])
        columns={'beta':ols.beta,'alpha':ols.alpha,'adaptive_residual':adaptive_residual,'adaptive_residual_vol':ols.residual_vol,
                 'beta_se_descriptive':ols.beta_se,
                 'beta_deviation':ols.beta-model['beta'],
                 'beta_recent_change':ols.beta-ols.beta.shift(20),
                 'beta_history_standardized':(ols.beta-ols.beta.shift(1).rolling(w).mean()).abs()/history_sd.where(history_sd>1e-12),
                 'beta_instability':(ols.beta-model['beta']).abs()/ols.beta_se.where(ols.beta_se>1e-12),
                 'phi':phi,'lambda':phi-1,'half_life':half_life(phi),
                 'oscillatory':(phi<0).where(phi.notna()),
                 'invalid_half_life':(~((phi>0)&(phi<1))).where(phi.notna()),
                 'ar_residual_vol':ar.residual_vol,'phi_se_descriptive':ar.beta_se,
                 'phi_low_descriptive':phi-1.96*ar.beta_se,
                 'phi_high_descriptive':phi+1.96*ar.beta_se,
                 'half_life_low_descriptive':half_life(phi-1.96*ar.beta_se),
                 'half_life_high_descriptive':half_life(phi+1.96*ar.beta_se)}
        for name,value in columns.items():
            out[f'{name}_{w}']=value
    return out.replace([np.inf,-np.inf],np.nan)
