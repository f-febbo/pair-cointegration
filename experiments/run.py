"""Run the whole declared batch; never stop selectively at a positive result."""
import argparse
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from sector_pairs.config import Config
from sector_pairs.data import load_prices,chronology,sha256
from sector_pairs.cointegration import spread
from sector_pairs.strategy import run_strategy,trade_ledger
from sector_pairs.diagnostics import indicators
from sector_pairs.performance import metrics,portfolio
from sector_pairs.evaluation import block_mean_interval
from .engine import simulate
from .strategies import specifications

def rolling_threshold(feature,days=252):
    return feature.rolling(days,min_periods=126).quantile(.90).shift(1)

def build_folds(index,n_is,test_start):
    folds=[];start=n_is+252;number=0
    while start<len(index):
        stop=min(start+252,len(index))
        boundary=int(index.searchsorted(test_start))
        if start<boundary<stop:stop=boundary
        number+=1
        folds.append(dict(name=f'fold_{number}',start=str(index[start].date()),end=str(index[stop-1].date()),
                          retrospective_test=bool(index[start]>=test_start)))
        start=stop
    return folds

def run(data='data/yahoo_20261016/adjusted_close.csv',output='reports/iterations'):
    config=Config();output=Path(output);output.mkdir(parents=True,exist_ok=True)
    daily=output/'daily';daily.mkdir(exist_ok=True)
    prices,n_is,audit=load_prices(data,config)
    stages,bounds=chronology(prices.index,n_is)
    models=pd.read_csv('reports/run/historical_nine_models.csv')
    # Independently validate loaded frozen models against the current snapshot.
    for _,m in models.iterrows():
        x=np.log(prices[m.x].iloc[:n_is]);y=np.log(prices[m.y].iloc[:n_is])
        b,a=np.polyfit(x,y,1)
        np.testing.assert_allclose([a,b],[m.alpha,m.beta],atol=1e-10,rtol=1e-10)
    specs=specifications();deployment=n_is+252
    (output/'batch_protocol.json').write_text(json.dumps({'specifications':specs,'deployment':str(prices.index[deployment].date()),
        'source_sha256':sha256(data),'protocol_sha256':sha256('experiments/protocol.md'),
        'holdout_status':'Previously viewed; retrospective exploratory evaluation only','bounds':bounds},indent=2))
    features={};controls={};frames={};portfolios={};ledger_counts={};threshold_rows=[]
    for kind in ('static','rolling'):
        control_pairs=[]
        for _,m in models.iterrows():
            control=run_strategy(prices,m,config,kind,n_is,executable_costs=True)
            controls[(m.pair,kind)]=control;control_pairs.append(control)
            ft=indicators(prices,m,config,control)
            ft.loc[stages=='selection']=np.nan
            features[(m.pair,kind)]=ft
        portfolios['control_'+kind]=portfolio(control_pairs).iloc[n_is:]
    for spec in specs:
        pairs=[];pair_ledger=[]
        for _,m in models.iterrows():
            kwargs={};kind=spec['control']
            if 'local_quantile_days' in spec:
                feature=features[(m.pair,kind)].beta_instability_252
                threshold=rolling_threshold(feature,spec['local_quantile_days'])
                kwargs['high']=feature>threshold;kwargs['action']=spec['action']
                threshold_rows.append(pd.DataFrame({'date':prices.index,'pair':m.pair,'strategy':spec['name'],
                                                   'feature':feature,'threshold_from_prior_history':threshold}))
            if 'mean_days' in spec:
                s=spread(prices,m)
                kwargs['alternative_z']=(s-s.rolling(spec['mean_days']).mean())/m.sigma
            for key in ('max_holding','reset_after_timeout'):
                if key in spec:kwargs[key]=spec[key]
            f=simulate(prices,m,config,kind,n_is,deployment,**kwargs)
            frames[(spec['name'],m.pair)]=f;pairs.append(f)
            ledger=trade_ledger(f).assign(pair=m.pair,strategy=spec['name'])
            pair_ledger.append(ledger)
        portfolios[spec['name']]=portfolio(pairs).iloc[n_is:]
        ledger_counts[spec['name']]=pd.concat(pair_ledger,ignore_index=True)
    all_metrics=[];attribution=[];inference=[]
    rng=np.random.default_rng(config.seed)
    for name,f in portfolios.items():f.to_csv(daily/f'{name}.csv',index_label='date')
    for spec in specs:
        name=spec['name'];kind=spec['control'];f=portfolios[name];base=portfolios['control_'+kind]
        ledger=ledger_counts[name];ledger.to_csv(output/f'{name}_trades.csv',index=False)
        for stage in ('development','validation','test'):
            ix=prices.index[stages==stage]
            actual=f.loc[ix];control=base.loc[ix]
            # Capital-match factor uses only the immediately preceding stage.
            prior='development' if stage=='validation' else ('validation' if stage=='test' else None)
            if prior:
                prior_ix=prices.index[stages==prior]
                ratio=f.loc[prior_ix,'exposure'].mean()/base.loc[prior_ix,'exposure'].mean()
                ratio=min(1.,max(0.,ratio))
            else:ratio=np.nan
            scaled=control.copy()
            for c in scaled.columns:scaled[c]*=ratio
            am=metrics(actual);bm=metrics(control)
            entries=sum(int(frames[(name,pair)].loc[ix,'entry'].sum()) for pair in models.pair)
            timeouts=sum(int(frames[(name,pair)].loc[ix,'timeout'].sum()) for pair in models.pair)
            completed=int((ledger.completed & ledger.exit_date.isin(ix)).sum())
            for cost_multiplier in (1.,2.):
                stressed=actual.copy();stressed['cost']=actual.cost*cost_multiplier
                stressed['net']=actual.gross-stressed.cost
                base_stress=control.copy();base_stress['net']=control.gross-control.cost*cost_multiplier
                result=metrics(stressed);bm_stress=metrics(base_stress)
                matched_stress=scaled.copy()
                if prior:
                    matched_stress['net']=base_stress.net*ratio
                all_metrics.append(dict(strategy=name,family=spec['family'],control=kind,stage=stage,cost_bps=int(5*cost_multiplier),
                                        entries=entries,completed_trades=completed,timeouts=timeouts,
                                        delta_return=result['return']-bm_stress['return'],delta_sharpe=result['sharpe']-bm_stress['sharpe'],
                                        control_return=bm_stress['return'],control_sharpe=bm_stress['sharpe'],control_drawdown=bm_stress['max_drawdown'],
                                        risk_scale_from_prior_stage=ratio,
                                        risk_scaled_control_return=metrics(matched_stress)['return'] if prior else np.nan,**result))
            if stage in ('validation','test'):
                difference=actual.net-control.net
                fit=sm.OLS(difference.to_numpy(),np.ones((len(difference),1))).fit(cov_type='HAC',cov_kwds={'maxlags':60})
                lo,hi=block_mean_interval(difference,60,config.bootstrap_reps,rng)
                inference.append(dict(strategy=name,family=spec['family'],stage=stage,n_dates=len(difference),mean_daily_net_advantage=difference.mean(),
                                      annualized_mean_advantage=252*difference.mean(),ci_low=lo,ci_high=hi,p_value=fit.pvalues[0],
                                      independent_blocks_approx=len(difference)/60))
            for _,m in models.iterrows():
                pf=frames[(name,m.pair)].loc[ix];pc=controls[(m.pair,kind)].loc[ix]
                attribution.append(dict(strategy=name,family=spec['family'],stage=stage,pair=m.pair,
                                        delta_return=metrics(pf)['return']-metrics(pc)['return'],**metrics(pf)))
    result=pd.DataFrame(all_metrics);result.to_csv(output/'strategy_metrics.csv',index=False)
    tests=pd.DataFrame(inference);tests['q_holm']=np.nan
    for stage in ('validation','test'):
        ix=tests.stage==stage;tests.loc[ix,'q_holm']=multipletests(tests.loc[ix,'p_value'],method='holm')[1]
    tests.to_csv(output/'paired_inference.csv',index=False)
    pd.DataFrame(attribution).to_csv(output/'pair_attribution.csv',index=False)
    folds=build_folds(prices.index,n_is,pd.Timestamp(bounds['test']['start']))
    fold_rows=[]
    for fold in folds:
        for spec in specs:
            f=portfolios[spec['name']].loc[fold['start']:fold['end']]
            control=portfolios['control_'+spec['control']].loc[fold['start']:fold['end']]
            fm=metrics(f);bm=metrics(control)
            fold_rows.append(dict(strategy=spec['name'],family=spec['family'],**fold,
                                  delta_return=fm['return']-bm['return'],delta_sharpe=fm['sharpe']-bm['sharpe'],**fm))
    fold_table=pd.DataFrame(fold_rows);fold_table.to_csv(output/'walk_forward.csv',index=False)
    pd.concat(threshold_rows,ignore_index=True).dropna().to_csv(output/'local_thresholds.csv.gz',index=False,compression='gzip') if threshold_rows else None
    for family,g in result.groupby('family'):
        target=output/'families'/family;target.mkdir(parents=True,exist_ok=True)
        g.to_csv(target/'metrics.csv',index=False)
        pd.DataFrame(attribution).query('family==@family').to_csv(target/'pair_attribution.csv',index=False)
        fold_table.query('family==@family').to_csv(target/'walk_forward.csv',index=False)
    from .report import write_report
    write_report(output,result,tests,fold_table,portfolios,bounds,specs)
    manifest={'source_sha256':sha256(data),'config':config.to_dict(),'code_sha256':{str(p):sha256(p) for p in Path('experiments').rglob('*.py')},
              'specifications':specs,'number_of_candidates':len(specs),'future_data_used':False}
    (output/'run_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(result[(result.stage.isin(['validation','test']))&(result.cost_bps==5)][['strategy','stage','return','sharpe','delta_return','delta_sharpe']].to_string(index=False),flush=True)
    return result

def main():
    os.environ.setdefault('MPLCONFIGDIR',str(Path.cwd()/'.mplconfig'))
    parser=argparse.ArgumentParser();parser.add_argument('--data',default='data/yahoo_20261016/adjusted_close.csv');parser.add_argument('--output',default='reports/iterations')
    args=parser.parse_args();run(args.data,args.output)

if __name__=='__main__':main()
