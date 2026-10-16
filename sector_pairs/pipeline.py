import json
import platform
import importlib.metadata
from pathlib import Path
import numpy as np
import pandas as pd
from .config import Config
from .data import load_prices, chronology, sha256
from .cointegration import select_pairs, models_for_reference, frozen_oos_adf, spread
from .strategy import run_strategy, trade_ledger
from .performance import metrics, portfolio
from .reference import compare_pairs, PORTFOLIO

def write_json(path,value):
    Path(path).write_text(json.dumps(value,indent=2,default=str))

def baseline(path, output, config=None):
    config=config or Config(); output=Path(output);output.mkdir(parents=True,exist_ok=True)
    prices,n_is,audit=load_prices(path,config)
    labels,bounds=chronology(prices.index,n_is)
    write_json(output/'data_audit.json',audit);write_json(output/'chronology.json',bounds)
    selection=select_pairs(prices,n_is)
    selection.to_csv(output/'all_55_pairs.csv',index=False)
    models=models_for_reference(prices,n_is,selection)
    models.to_csv(output/'historical_nine_models.csv',index=False)
    rows=[];frames={};portfolios={};portfolio_rows=[]
    for _,model in models.iterrows():
        row=model.to_dict();row.update(frozen_oos_adf(spread(prices,model),n_is))
        for strategy in ('static','rolling'):
            f=run_strategy(prices,model,config,strategy,start=n_is,return_convention='reference_log')
            frames[(model.pair,strategy)]=f
            trade_ledger(f).to_csv(output/(model.pair.replace('/','_')+'_'+strategy+'_trades.csv'),index=False)
            f.to_csv(output/(model.pair.replace('/','_')+'_'+strategy+'_baseline.csv'),index_label='date')
            for k,v in metrics(f.iloc[n_is:]).items():row[f'{strategy}_{k}']=v
            ledger=trade_ledger(f)
            row[f'{strategy}_completed_trades']=int(ledger.completed.sum())
            row[f'{strategy}_open_trades']=int((~ledger.completed).sum())
            row[f'{strategy}_entries']=int(f.entry.sum())
        rows.append(row)
    actual=pd.DataFrame(rows)
    actual.to_csv(output/'baseline_pair_metrics.csv',index=False)
    comparison=compare_pairs(actual)
    comparison.to_csv(output/'baseline_replication_differences.csv',index=False)
    for strategy in ('static','rolling'):
        f=portfolio([frames[(p,strategy)] for p in models.pair])
        portfolios[(strategy,'control')]=f.iloc[n_is:]
        f.to_csv(output/f'{strategy}_historical_nine_portfolio.csv',index_label='date')
        # IS results are only fitted retrospective context, never independent evidence.
        insample=portfolio([run_strategy(prices.iloc[:n_is],m,config,strategy,return_convention='reference_log') for _,m in models.iterrows()])
        for stage,g in [('selection',insample),('oos',f.iloc[n_is:])]:
            met=metrics(g)
            rec=dict(strategy=strategy,stage=stage,universe='historical_nine',**met)
            for key,value in PORTFOLIO[(strategy,stage)].items():
                rec[f'reference_{key}']=value;rec[f'delta_{key}']=met[key]-value
                rec[f'absolute_delta_{key}']=abs(met[key]-value)
                rec[f'relative_delta_{key}']=(met[key]-value)/abs(value)
            portfolio_rows.append(rec)
        selected=selection[selection.selected]
        if not selected.empty:
            dynamic=portfolio([run_strategy(prices,m,config,strategy,start=n_is,return_convention='reference_log') for _,m in selected.iterrows()]).iloc[n_is:]
            dynamic.to_csv(output/f'{strategy}_reproduced_selection_portfolio.csv',index_label='date')
            portfolio_rows.append(dict(strategy=strategy,stage='oos',universe='reproduced_selection',**metrics(dynamic)))
    ptable=pd.DataFrame(portfolio_rows);ptable.to_csv(output/'baseline_portfolio_metrics.csv',index=False)
    reference_sets={frozenset((r.y,r.x)) for _,r in models.iterrows()}
    actual_sets={frozenset((r.y,r.x)) for _,r in selection[selection.selected].iterrows()}
    assessment={'pair_sets_match':reference_sets==actual_sets,
                'selected_count':int(selection.selected.sum()),
                'reference_only':['/'.join(sorted(x)) for x in reference_sets-actual_sets],
                'reproduced_only':['/'.join(sorted(x)) for x in actual_sets-reference_sets],
                'data_boundaries_match':audit['reference_boundaries_match'],
                'max_absolute_beta_difference':float(comparison[comparison.measure=='beta'].absolute_difference.max()),
                'max_absolute_pair_return_difference':float(comparison[comparison.measure.isin(['static_return','rolling_return'])].absolute_difference.max()),
                'exact_replication':False,
                'status':'Evaluated against rounded PDF values; discrepancies retained. Exact replication cannot be certified without original raw snapshot/code.'}
    write_json(output/'baseline_assessment.json',assessment)
    from .reporting import baseline_report
    baseline_report(output,audit,assessment,actual,ptable,selection)
    print('Baseline evaluated:',json.dumps(assessment),flush=True)
    return prices,n_is,audit,labels,bounds,selection,models,frames,portfolios

def research(path, output, config=None):
    config=config or Config();output=Path(output)
    state=baseline(path,output,config)
    prices,n_is,audit,labels,bounds,selection,models,frames,portfolios=state
    # This point is reached only after baseline comparison and assessment are written.
    # Reference P&L compounds normalized log-spread increments as daily returns.
    # Prospective trading comparisons use simple leg returns; retain both controls.
    portfolios={(k,'reference_log_control'):v for (k,_),v in portfolios.items()}
    frames={(m.pair,k):run_strategy(prices,m,config,k,n_is) for _,m in models.iterrows() for k in ('static','rolling')}
    for k in ('static','rolling'):
        portfolios[(k,'control')]=portfolio([frames[(p,k)] for p in models.pair]).iloc[n_is:]
    from .diagnostics import indicators
    from .outcomes import forward_outcomes,purge_labels
    from .evaluation import evaluate
    from .figures import pair_figures,overview
    panels=[];feature_sets={};thresholds=[];strategy_rows=[];attribution=[];alarms=[]
    figure_dir=output/'figures';figure_dir.mkdir(exist_ok=True)
    modified_frames={}
    for _,m in models.iterrows():
        for strategy in ('static','rolling'):
            frame=frames[(m.pair,strategy)]
            features=indicators(prices,m,config,frame)
            feature_sets[(m.pair,strategy)]=features
            features.loc[labels!='selection'].to_csv(output/(m.pair.replace('/','_')+'_'+strategy+'_indicators.csv'),index_label='date')
            for h in config.horizons:
                outcomes=forward_outcomes(prices,m,config,frame,h)
                for w in config.windows:
                    rename={col:col.rsplit('_',1)[0] for col in features if col.endswith('_'+str(w))}
                    chosen=features[rename.keys()].rename(columns=rename).join(features[['abs_z','recent_vol','recent_spread_return','trailing_convergence']])
                    panel=chosen.join(outcomes,how='inner').assign(pair=m.pair,strategy=strategy,window=w).reset_index(names='date')
                    panels.append(panel)
            if strategy=='static':
                pair_figures(figure_dir,m.pair,frame,features,m,bounds,labels)
    panel=purge_labels(pd.concat(panels,ignore_index=True),bounds)
    panel=panel[panel.date>=pd.Timestamp(bounds['development']['start'])].reset_index(drop=True)
    coverage=[]
    for (k,w,h,stage,pair),g in panel.groupby(['strategy','window','horizon','stage','pair']):
        base=['abs_z','recent_vol','recent_spread_return','trailing_convergence','convergence']
        coverage.append(dict(strategy=k,window=w,horizon=h,stage=stage,pair=pair,
                             n=len(g),complete_baseline=int(g[base].notna().all(axis=1).sum()),
                             missing_trailing_convergence=int(g.trailing_convergence.isna().sum()),
                             near_zero=int(g.near_zero_deviation.sum()),
                             actual_entries=int(g.entry_opportunity.sum()),existing_positions=int(g.existing_position.sum())))
    pd.DataFrame(coverage).to_csv(output/'predictive_coverage.csv',index=False)
    panel.to_csv(output/'predictive_panel.csv.gz',index=False,compression='gzip')
    print('Causal panel built; evaluating predictive validity.',flush=True)
    predictive,quantiles,forecasts=evaluate(panel,config)
    predictive.to_csv(output/'predictive_results.csv',index=False)
    quantiles.to_csv(output/'quantile_results.csv',index=False)
    forecasts.to_csv(output/'primary_forecasts.csv',index=False)
    print('Predictive validity evaluated; applying frozen trading modifications.',flush=True)
    # No performance-based feature/threshold selection. All declared variants retained.
    variants={'beta_entry':('beta_instability_252','entry_filter'),
              'beta_reduction':('beta_instability_252','reduction'),
              'vol_entry':('recent_vol','entry_filter'),
              'beta126_entry':('beta_instability_126','entry_filter'),
              'beta504_entry':('beta_instability_504','entry_filter'),
              'phi_entry':('phi_252','entry_filter')}
    dev=labels=='development'; deployment=labels.isin(['validation','test'])
    for strategy in ('static','rolling'):
        for variant,(column,action) in variants.items():
            new_frames=[]
            for _,m in models.iterrows():
                fts=feature_sets[(m.pair,strategy)]
                threshold=fts.loc[dev,column].quantile(config.filter_quantile)
                if not np.isfinite(threshold):raise ValueError(f'No valid calibration for {m.pair}/{column}')
                high=(fts[column]>threshold)&deployment
                thresholds.append(dict(pair=m.pair,strategy=strategy,variant=variant,feature=column,threshold=threshold,quantile=config.filter_quantile,calibration_start=bounds['development']['start'],calibration_end=bounds['development']['end']))
                modified=run_strategy(prices,m,config,strategy,n_is,high,action)
                modified_frames[(m.pair,strategy,variant)]=modified
                new_frames.append(modified)
                modified.to_csv(output/(m.pair.replace('/','_')+'_'+strategy+'_'+variant+'.csv'),index_label='date')
                ledger=trade_ledger(modified)
                ledger.to_csv(output/(m.pair.replace('/','_')+'_'+strategy+'_'+variant+'_trades.csv'),index=False)
                base=frames[(m.pair,strategy)]
                base_ledger=trade_ledger(base)
                for stage in ('validation','test'):
                    mask=labels==stage
                    # Matured baseline trades only for counterfactual hit/miss summaries.
                    stage_trades=base_ledger[(base_ledger.entry_date>=pd.Timestamp(bounds[stage]['start'])) & (base_ledger.entry_date<=pd.Timestamp(bounds[stage]['end']))].copy()
                    stage_trades['flagged']=high.reindex(pd.DatetimeIndex(stage_trades.entry_date)).to_numpy()
                    observed=stage_trades[stage_trades.flagged & stage_trades.completed & (stage_trades.exit_date<=pd.Timestamp(bounds[stage]['end']))]
                    alarms.append(dict(pair=m.pair,strategy=strategy,variant=variant,stage=stage,
                                       signal_frequency=float(high[mask].mean()),baseline_entries=len(stage_trades),
                                       flagged_baseline_entries=int(stage_trades.flagged.sum()),
                                       suppression_fraction=float(stage_trades.flagged.mean()) if len(stage_trades) else np.nan,
                                       matured_flagged_trades=len(observed),
                                       flagged_unresolved=int(stage_trades.flagged.sum())-len(observed),
                                       missed_profitable_recoveries=int((observed.net_return>0).sum()),
                                       avoided_losses=int((observed.net_return<=0).sum()),
                                       mean_suppressed_trade_return=observed.net_return.mean(),
                                       actual_filter_denied_days=int(modified.loc[mask,'suppressed'].sum())))
                    bm=metrics(base.loc[mask]);mm=metrics(modified.loc[mask])
                    attribution.append(dict(pair=m.pair,strategy=strategy,variant=variant,stage=stage,
                                            delta_return=mm['return']-bm['return'],delta_sharpe=mm['sharpe']-bm['sharpe'],
                                            completed_trades=int(((ledger.exit_date>=pd.Timestamp(bounds[stage]['start'])) & (ledger.exit_date<=pd.Timestamp(bounds[stage]['end'])) & ledger.completed).sum()),
                                            **mm))
            portfolios[(strategy,variant)]=portfolio(new_frames).iloc[n_is:]
        # Cost and window/boundary sensitivities are predeclared, not used for selection.
        portfolios[(strategy,'executable_cost_control')]=portfolio([run_strategy(prices,m,config,strategy,n_is,executable_costs=True) for _,m in models.iterrows()]).iloc[n_is:]
        carry_frames=[]
        for _,m in models.iterrows():
            f=run_strategy(prices,m,config,strategy,0)
            modified_frames[(m.pair,strategy,'carry_from_is_control')]=f;carry_frames.append(f)
        portfolios[(strategy,'carry_from_is_control')]=portfolio(carry_frames).iloc[n_is:]
        if strategy=='rolling':
            calendar_frames=[]
            for _,m in models.iterrows():
                f=run_strategy(prices,m,config,'calendar3y',n_is)
                modified_frames[(m.pair,strategy,'calendar3y_control')]=f;calendar_frames.append(f)
            portfolios[(strategy,'calendar3y_control')]=portfolio(calendar_frames).iloc[n_is:]
        # Freeze baseline risk scaling using validation utilization; compare in test only.
        ix=prices.index[labels=='validation']
        base=portfolios[(strategy,'control')]
        ratio=portfolios[(strategy,'beta_entry')].loc[ix,'exposure'].mean()/base.loc[ix,'exposure'].mean()
        scaled=base.copy()
        for col in ['net','gross','cost','exposure','turnover']:scaled[col]*=ratio
        portfolios[(strategy,'risk_scaled_control')]=scaled
        for variant in ['beta_entry','beta_reduction','vol_entry']:
            # Same modifications under daily leg rebalancing costs.
            fs=[]
            for _,m in models.iterrows():
                high=modified_frames[(m.pair,strategy,variant)].high
                fs.append(run_strategy(prices,m,config,strategy,n_is,high,variants[variant][1],True))
            portfolios[(strategy,variant+'_executable_cost')]=portfolio(fs).iloc[n_is:]
    for (strategy,variant),f in portfolios.items():
        f.to_csv(output/f'{strategy}_{variant}_portfolio.csv',index_label='date')
        for stage in ('development','validation','test'):
            if variant=='risk_scaled_control' and stage!='test':continue
            mask=labels.reindex(f.index)==stage
            mets=metrics(f.loc[mask])
            completed=0;entries=0
            for pair in models.pair:
                if variant in ('control','reference_log_control','executable_cost_control','risk_scaled_control'):
                    source=frames[(pair,strategy)]
                else:
                    source=modified_frames.get((pair,strategy,variant.removesuffix('_executable_cost')))
                if source is not None:
                    entries+=int(source.loc[labels==stage,'entry'].sum())
                    ledger=trade_ledger(source)
                    completed+=int((ledger.completed & (ledger.exit_date>=pd.Timestamp(bounds[stage]['start'])) & (ledger.exit_date<=pd.Timestamp(bounds[stage]['end']))).sum())
            strategy_rows.append(dict(strategy=strategy,variant=variant,stage=stage,entries=entries,completed_trades=completed,**mets))
    strategy_table=pd.DataFrame(strategy_rows);attribution=pd.DataFrame(attribution);alarms=pd.DataFrame(alarms)
    strategy_table.to_csv(output/'strategy_results.csv',index=False)
    attribution.to_csv(output/'pair_attribution.csv',index=False)
    alarms.to_csv(output/'signal_analysis.csv',index=False)
    pd.DataFrame(thresholds).to_csv(output/'frozen_thresholds.csv',index=False)
    overview(figure_dir,panel,quantiles,portfolios,attribution,alarms,bounds)
    provenance={'config':config.to_dict(),'python':platform.python_version(),
                'packages':{x:importlib.metadata.version(x) for x in ['numpy','pandas','statsmodels','scipy','matplotlib','yfinance']},
                'input_sha256':sha256(path),'protocol_sha256':sha256('docs/research_protocol.md'),
                'code_sha256':{str(p):sha256(p) for p in Path('sector_pairs').glob('*.py')}}
    write_json(output/'run_manifest.json',provenance)
    from .reporting import research_report
    research_report(output,audit,bounds,predictive,strategy_table,alarms,config)
    print('Research complete:',output/'research_report.md',flush=True)
    return strategy_table
