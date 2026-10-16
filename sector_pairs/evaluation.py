"""Interpretable forecasting, development-only scaling, shared-date inference."""
import numpy as np
import pandas as pd
from scipy.stats import norm, spearmanr
from scipy.linalg import qr
from statsmodels.stats.multitest import multipletests
import statsmodels.api as sm

BASE=['abs_z','recent_vol','recent_spread_return','trailing_convergence']
OUTCOMES=['convergence','converged','adverse_excursion','convergence_time_capped','trade_return','adverse_trade','future_phi']

def independent_columns(frame):
    """Remove unidentified nuisance directions, without silently dropping the tested feature."""
    a=frame.to_numpy(dtype=float)
    _,r,pivots=qr(a,mode='economic',pivoting=True)
    diagonal=np.abs(np.diag(r))
    tolerance=max(a.shape)*np.finfo(float).eps*(diagonal.max() if len(diagonal) else 0)
    rank=int((diagonal>tolerance).sum())
    keep=set(frame.columns[np.sort(pivots[:rank])])
    return [col for col in frame.columns if col in keep]

def date_hac(fit, dates, lag, calendar=None):
    """HAC of date-aggregated score vectors includes simultaneous shared-ETF dependence."""
    x=np.asarray(fit.model.exog); u=np.asarray(fit.resid)
    scores=pd.DataFrame(x*u[:,None]).groupby(np.asarray(dates)).sum().sort_index()
    if calendar is not None:
        scores=scores.reindex(pd.DatetimeIndex(calendar),fill_value=0)
    scores=scores.to_numpy()
    meat=scores.T@scores
    for k in range(1,min(lag,len(scores)-1)+1):
        cross=scores[k:].T@scores[:-k]
        meat+=(1-k/(lag+1))*(cross+cross.T)
    bread=np.linalg.pinv(x.T@x)
    se=np.sqrt(np.maximum(0,np.diag(bread@meat@bread)))
    return se

def block_mean_interval(values, block, reps, rng):
    """Circular moving-date bootstrap; whole cross-section already date averaged."""
    v=np.asarray(values); n=len(v)
    if n<2*block:
        return np.nan,np.nan
    means=[]
    for _ in range(reps):
        starts=rng.integers(0,n,size=int(np.ceil(n/block)))
        picks=((starts[:,None]+np.arange(block))%n).ravel()[:n]
        sampled=v[picks]
        means.append(np.nanmean(sampled) if np.isfinite(sampled).any() else np.nan)
    return tuple(np.nanquantile(means,[.025,.975]))

def evaluate(panel, config):
    rows=[]; quantiles=[]; forecasts=[]
    rng=np.random.default_rng(config.seed)
    for (strategy,w,h), group in panel.groupby(['strategy','window','horizon'],sort=True):
        for feature in ('beta_instability','phi'):
            for population in ('all_dates','entry','existing'):
                g=group if population=='all_dates' else group[group['entry_opportunity' if population=='entry' else 'existing_position']]
                outcomes=OUTCOMES if population=='all_dates' else (['trade_return','adverse_trade'] if population=='entry' else ['existing_return'])
                for outcome in outcomes:
                    columns=BASE+[feature,outcome,'pair','date','stage']
                    d=g[columns].replace([np.inf,-np.inf],np.nan).dropna()
                    train=d[d.stage=='development']; test=d[d.stage=='test']
                    if len(train)<80 or len(test)<30:
                        rows.append(dict(strategy=strategy,window=w,horizon=h,feature=feature,population=population,outcome=outcome,status='insufficient complete observations'))
                        continue
                    predictors=BASE+[feature]
                    # Robust clipping limits fixed on development data, not on holdout.
                    low=train[predictors].quantile(.01); high=train[predictors].quantile(.99)
                    mu=train[predictors].clip(low,high,axis=1).mean()
                    sd=train[predictors].clip(low,high,axis=1).std().replace(0,1)
                    scaled=(d[predictors].clip(low,high,axis=1)-mu)/sd
                    pairs=sorted(train.pair.unique())
                    dummy=pd.DataFrame({f'pair_{p}':(d.pair==p).astype(float) for p in pairs[1:]},index=d.index)
                    xb=sm.add_constant(pd.concat([scaled[BASE],dummy],axis=1),has_constant='add')
                    ti=d.stage=='development'
                    xb=xb[independent_columns(xb.loc[ti])]
                    xe=pd.concat([xb,scaled[[feature]]],axis=1)
                    if np.linalg.matrix_rank(xe.loc[ti].to_numpy())<=len(xb.columns):
                        rows.append(dict(strategy=strategy,window=w,horizon=h,feature=feature,population=population,outcome=outcome,status='unidentified incremental feature'))
                        continue
                    fit_base=sm.OLS(d.loc[ti,outcome],xb.loc[ti]).fit()
                    fit_ext=sm.OLS(d.loc[ti,outcome],xe.loc[ti]).fit()
                    cuts=np.unique(train[feature].quantile([0,.2,.4,.6,.8,1]).to_numpy())
                    # Holdout values outside development range go in extreme groups.
                    if len(cuts)>2:
                        cuts[0]=-np.inf; cuts[-1]=np.inf
                    for stage in ('validation','test'):
                        mask=(d.stage==stage)&d.pair.isin(pairs)
                        if mask.sum()<30:
                            continue
                        actual=d.loc[mask,outcome]
                        base=fit_base.predict(xb.loc[mask]); extended=fit_ext.predict(xe.loc[mask])
                        # Linear probability forecasts, clipped to [0,1], use Brier score.
                        binary=outcome in ('converged','adverse_trade')
                        if binary:
                            base=base.clip(0,1); extended=extended.clip(0,1)
                        loss=(actual-base)**2-(actual-extended)**2
                        dates=d.loc[mask,'date']
                        daily=loss.groupby(dates.to_numpy()).mean().sort_index()
                        calendar=pd.DatetimeIndex(sorted(group.loc[group.stage==stage,'date'].unique()))
                        daily_calendar=daily.reindex(calendar)
                        lag=max(60,h)
                        if len(daily)>lag+2:
                            lm=sm.OLS(daily.to_numpy(),np.ones((len(daily),1))).fit()
                            lm_se=date_hac(lm,daily.index,lag,calendar)[0]
                            p_gain=float(2*norm.sf(abs(lm.params[0]/lm_se))) if lm_se>0 else np.nan
                        else:
                            p_gain=np.nan
                        lo,hi=block_mean_interval(daily_calendar,lag,config.bootstrap_reps,rng)
                        # Descriptive holdout partial association; forecasting fit stays frozen.
                        assoc_base=xb.loc[mask]
                        assoc_base=assoc_base[independent_columns(assoc_base)]
                        assoc_x=pd.concat([assoc_base,scaled.loc[mask,[feature]]],axis=1)
                        if np.linalg.matrix_rank(assoc_x.to_numpy())>len(assoc_base.columns):
                            assoc=sm.OLS(actual,assoc_x).fit()
                            se=date_hac(assoc,dates,lag,calendar)[-1]
                            coef=assoc.params.iloc[-1]
                            p_assoc=2*norm.sf(abs(coef/se)) if se>0 else np.nan
                        else:
                            coef=se=p_assoc=np.nan
                        rho=spearmanr(d.loc[mask,feature],actual).statistic if actual.nunique()>1 and d.loc[mask,feature].nunique()>1 else np.nan
                        base_losses=(actual-base)**2
                        extended_losses=(actual-extended)**2
                        row=dict(strategy=strategy,window=w,horizon=h,feature=feature,population=population,
                                 outcome=outcome,stage=stage,status='evaluated',n_train=int(ti.sum()),n=int(mask.sum()),
                                 n_dates=len(daily),independent_blocks_approx=len(daily)/lag,
                                 baseline_mse=base_losses.groupby(dates.to_numpy()).mean().mean(),extended_mse=extended_losses.groupby(dates.to_numpy()).mean().mean(),
                                 mse_gain=daily.mean(),gain_ci_low=lo,gain_ci_high=hi,p_gain=p_gain,
                                 coefficient=coef,development_coefficient=fit_ext.params.iloc[-1],se_date_hac=se,p_association=p_assoc,rank_correlation=rho,
                                 primary=bool(w==252 and h==20 and population=='all_dates' and outcome=='convergence'))
                        rows.append(row)
                        if len(cuts)>2:
                            bins=pd.cut(d.loc[mask,feature],cuts,labels=False,include_lowest=True)
                            for q, ids in bins.groupby(bins).groups.items():
                                quantiles.append(dict(strategy=strategy,window=w,horizon=h,feature=feature,population=population,
                                                      outcome=outcome,stage=stage,quantile=int(q)+1,n=len(ids),mean=d.loc[ids,outcome].mean()))
                        if w==252 and h==20 and population=='all_dates' and outcome=='convergence':
                            forecasts.append(pd.DataFrame({'date':dates,'pair':d.loc[mask,'pair'],'strategy':strategy,'feature':feature,'stage':stage,'actual':actual,'baseline':base,'extended':extended}))
    results=pd.DataFrame(rows)
    for p,q in [('p_gain','q_gain_by'),('p_association','q_association_by')]:
        results[q]=np.nan
        if p in results:
            valid=results[p].notna() & (results.stage=='test')
            results.loc[valid,q]=multipletests(results.loc[valid,p],method='fdr_by')[1] if valid.any() else []
    results['q_primary_gain_holm']=np.nan
    if 'primary' in results:
        primary=results.primary.fillna(False) & (results.stage=='test') & results.p_gain.notna()
        if primary.any():
            results.loc[primary,'q_primary_gain_holm']=multipletests(results.loc[primary,'p_gain'],method='holm')[1]
    return results,pd.DataFrame(quantiles),pd.concat(forecasts,ignore_index=True) if forecasts else pd.DataFrame()
