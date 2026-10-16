import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def write_report(output,results,tests,folds,portfolios,bounds,specs):
    output=Path(output)
    val=results[(results.stage=='validation')&(results.cost_bps==5)].copy()
    stress=results[(results.stage=='validation')&(results.cost_bps==10)].set_index('strategy')
    candidates=val[(val.delta_return>0)&(val.delta_sharpe>0)&(val.max_drawdown>=val.control_drawdown-.01)].copy()
    candidates=candidates[candidates.strategy.map(stress.delta_return)>0]
    nominee=candidates.sort_values(['delta_sharpe','delta_return'],ascending=False).iloc[0] if len(candidates) else None
    nomination={'basis':'Validation net Sharpe improvement; positive return and ten-bp return improvement; drawdown deterioration at most one percentage point',
                'validation_start':bounds['validation']['start'],'validation_end':bounds['validation']['end'],
                'strategy':nominee.strategy if nominee is not None else None,
                'future_paper_start':'2026-10-19','holdout_status':'All historical checks are exploratory; previously viewed test is not independent.'}
    if nominee is not None:
        nomination['specification']=next(s for s in specs if s['name']==nominee.strategy)
    (output/'prospective_candidate.json').write_text(json.dumps(nomination,indent=2))
    main=results[(results.stage.isin(['validation','test']))&(results.cost_bps==5)].copy()
    main['positive_return_and_sharpe']=(main.delta_return>0)&(main.delta_sharpe>0)
    cols=['strategy','stage','return','sharpe','delta_return','delta_sharpe','max_drawdown','capital_utilization','risk_scaled_control_return','completed_trades','timeouts']
    positive_val=int(val.eval('delta_return>0 and delta_sharpe>0').sum())
    test=main[main.stage=='test']
    positive_test=int(test.positive_return_and_sharpe.sum())
    positive_in_both=set(main.query('stage=="validation" and positive_return_and_sharpe').strategy)&set(main.query('stage=="test" and positive_return_and_sharpe').strategy)
    inference=tests.copy()
    significant=inference[(inference.q_holm<.05)&(inference.mean_daily_net_advantage>0)&(inference.ci_low>0)]
    if nominee is not None:
        selected=main[main.strategy==nominee.strategy]
        detail='\n\n'+selected[cols].to_markdown(index=False,floatfmt='.4f')
        opening=f"The validation rule nominates **{nominee.strategy}** for future paper evaluation. It improves validation return by {nominee.delta_return:.2%} and Sharpe by {nominee.delta_sharpe:.3f}."
    else:
        detail='';opening='No candidate satisfies the fixed validation nomination rule.'
    robustness=folds.groupby('strategy').agg(folds=('name','size'),positive_return_folds=('delta_return',lambda s:int((s>0).sum())),positive_sharpe_folds=('delta_sharpe',lambda s:int((s>0).sum()))).reset_index()
    report=f'''# Exploratory strategy iterations: a positive backtest is not independent validation

{opening}

This batch contains {len(specs)} candidates fixed in [the iteration protocol](../../experiments/protocol.md) before batch execution. The previous historical holdout had already been examined. All results here are exploratory; no repeated search for statistical significance or concealed unsuccessful strategies is used. The original hypothesis and negative primary result in [the original study](../run/research_report.md) remain intact.

## What improved?

{positive_val} of {len(specs)} candidates improve both net cumulative return and Sharpe in validation; {positive_test} do so in the previously viewed test. {len(positive_in_both)} improve both metrics in both periods: {', '.join(sorted(positive_in_both)) if positive_in_both else 'none'}.

{opening}{detail}

## All candidates versus unchanged controls

All returns are simple adjusted leg returns, charging 5 bp on actual daily leg turnover. Reference-log approximations are not used. Frozen IS hedge ratios and sigma are retained. Local filters change threshold calibration only. Shorter means change equilibrium estimation only. Time-out/reset strategies explicitly add a risk-control exit and a rearm rule. These extensions do not modify the original replication.

{main[cols].to_markdown(index=False,floatfmt='.4f')}

Absolute returns are decimal fractions; delta_return is the difference in compounded returns, not an additive P&L attribution. Capital-use-matched controls use exposure ratios known before the evaluation period; they are not scaled using future realized volatility. Compare return, drawdown, utilization and matched-control returns together. Entry counts, turnover and arithmetic cost totals are in `strategy_metrics.csv`. Time-out counts identify forced exits. Completed trades use exit dates; final open positions remain marked to market.

## Economic gains versus statistical evidence

{len(significant)} paired net-return comparisons have a positive advantage, a positive block-bootstrap lower limit, and Holm q<0.05 across their ten-candidate stage family. Validation and retrospective test are corrected separately. The nominal significance family does not account for all earlier research and cannot make the reused test independent.

{inference[['strategy','stage','annualized_mean_advantage','ci_low','ci_high','p_value','q_holm','independent_blocks_approx']].to_markdown(index=False,floatfmt='.5f')}

Paired return differences are computed on common dates from equal allocated pair portfolios; shared ETF exposures are not treated as independent experiments. HAC uses 60 sessions; circular shared-date block bootstrap uses 499 replications. Each period has only about eight such blocks. These approximations assume sufficient weak dependence and condition on already chosen rules. A small positive economic backtest is insufficient to claim a general forecasting advantage.

## Walk-forward and transaction-cost sensitivity

{robustness.to_markdown(index=False)}

These consecutive 252-session folds begin after the initial 252 OOS sessions; a fold is split at the original test boundary. The final short fold is retained. Rules are not reselected per fold. See `walk_forward.csv` for every fold's return and drawdown. Val/test rows also compare five- and ten-basis-point costs for every candidate, without choosing the favorable cost assumption.

{results[(results.cost_bps==10)&results.stage.isin(['validation','test'])][['strategy','stage','return','sharpe','delta_return','delta_sharpe','transaction_costs']].to_markdown(index=False,floatfmt='.4f')}

![Complete family comparison](family_performance.png)

![Validation and previously viewed test improvement](validation_test_improvements.png)

## Interpretation and next evidence

A time-out/reset rule can improve performance by reducing exposure to a persistent deviation. It supplies no direct test that a statistical instability detector predicted the breakdown. Shorter means can alter opportunity frequency without explaining structural changes. Improvements from local calibration test whether a static threshold's vintage was unhelpful, not whether discrete market regimes exist. These mechanisms and their capital use must remain distinct.

The nominated strategy, if any, is frozen in `prospective_candidate.json` for paper evaluation starting October 19, 2026. It is nominated from validation only; its already viewed test results are disclosed rather than used to change its settings. No prospective performance has yet occurred in this study. No live trading orders are placed.

Reproduce with `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m experiments.run`. Daily portfolio series, trades, local thresholds, pair attribution, all negative cases, fixed specifications and code/data hashes are preserved. Three strategy families receive separate commits; neither a successful run nor a commit implies statistical validation.
'''
    (output/'report.md').write_text(report)
    summary=main[cols].to_markdown(index=False,floatfmt='.4f')
    (output/'summary.md').write_text(f'# Iteration summary\n\n{opening}\n\n{positive_val}/{len(specs)} improve validation return and Sharpe; {positive_test}/{len(specs)} improve the previously viewed test; {len(positive_in_both)} improve both periods. {len(significant)} paired comparisons meet the full stage-adjusted evidence rule. All historical results are exploratory.\n\n{summary}\n\n[Full analysis](report.md)\n')
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
    families=sorted({s['family'] for s in specs})
    fig,axs=plt.subplots(2,len(families),figsize=(16,8),sharex=True,squeeze=False)
    for row,kind in enumerate(('static','rolling')):
        for col,family in enumerate(families):
            ax=axs[row,col]
            base=portfolios['control_'+kind]
            ax.plot(base.index,(1+base.net).cumprod(),label='Control',color='black',lw=1.2)
            for spec in specs:
                if spec['family']==family and spec['control']==kind:
                    f=portfolios[spec['name']]
                    ax.plot(f.index,(1+f.net).cumprod(),label=spec['name'].removeprefix(kind+'_'),lw=1)
            for stage,color in [('validation','#bf871f'),('test','#a33042')]:
                ax.axvline(pd.Timestamp(bounds[stage]['start']),color=color,ls='--',lw=.8)
            ax.set_title(kind.title()+' | '+family.replace('_',' '));ax.legend(fontsize=7);ax.grid(alpha=.2)
            if col==0:ax.set_ylabel('Growth of $1, net of daily turnover costs')
    fig.tight_layout();fig.savefig(output/'family_performance.png');fig.savefig(output/'family_performance.pdf');plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(14,5))
    for ax,measure in zip(axs,['delta_return','delta_sharpe']):
        main.pivot(index='strategy',columns='stage',values=measure).plot.barh(ax=ax)
        ax.axvline(0,color='black',lw=.8);ax.set_title(measure.replace('_',' ').title()+' versus original control');ax.set_ylabel('');ax.grid(axis='x',alpha=.2)
    fig.tight_layout();fig.savefig(output/'validation_test_improvements.png');fig.savefig(output/'validation_test_improvements.pdf');plt.close(fig)
