from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def setup():
    plt.rcParams.update({'figure.dpi':120,'savefig.dpi':180,'font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'axes.grid':True,'grid.alpha':.2})

def boundaries(axes,bounds):
    axes=np.array(axes).ravel()
    for ax in axes:
        for stage,color in [('development','#777777'),('validation','#d28b21'),('test','#9f3544')]:
            date=pd.Timestamp(bounds[stage]['start'])
            ax.axvline(date,color=color,ls='--',lw=.8,label=stage+' start')
            if ax is axes[0]:
                ax.annotate(stage.title()+' start',xy=(date,.04),xycoords=('data','axes fraction'),
                            xytext=(3,0),textcoords='offset points',fontsize=8,color=color,rotation=90,
                            va='bottom',bbox={'facecolor':'white','alpha':.75,'edgecolor':'none','pad':1})

def save(fig,path):
    fig.tight_layout()
    fig.savefig(path.with_suffix('.png'),bbox_inches='tight')
    fig.savefig(path.with_suffix('.pdf'),bbox_inches='tight')
    plt.close(fig)

def pair_figures(directory,pair,frame,features,model,bounds,labels):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);setup()
    tag=pair.replace('/','_')
    fig,axs=plt.subplots(5,1,figsize=(13,14))
    axs[1].sharex(axs[0]);axs[3].sharex(axs[2]);axs[4].sharex(axs[2])
    for ax in (axs[0],axs[2],axs[3]):ax.tick_params(labelbottom=False)
    axs[0].plot(frame.index,frame.spread,label='Frozen OLS spread',lw=.8)
    axs[0].plot(frame.index,frame['mean'],label='Equilibrium',color='black',lw=.8)
    axs[0].set_ylabel('Log spread');axs[0].legend(loc='upper left')
    axs[0].set_title(pair+' | Original model and trailing descriptive diagnostics')
    axs[1].plot(frame.index,frame.z,lw=.8,label='Static z-score')
    for level in [-1.5,1.5]:axs[1].axhline(level,color='#9f3544',ls=':',lw=.8)
    axs[1].set_ylabel('z-score')
    # Frozen-reference diagnostics are meaningful prospectively after pair selection.
    f=features.loc[labels!='selection']
    for w in (126,252,504):
        axs[2].plot(f.index,f[f'beta_{w}'],label=str(w)+' days',lw=.8)
        axs[3].plot(f.index,f[f'phi_{w}'],label=str(w)+' days',lw=.7)
        axs[4].plot(f.index,f[f'half_life_{w}'].clip(upper=1000),label=str(w)+' days',lw=.7)
    axs[2].axhline(model['beta'],color='black',ls=':',label='Frozen beta')
    axs[2].set_ylabel('OLS beta');axs[2].legend(ncol=4)
    axs[3].axhline(1,color='black',ls=':');axs[3].set_ylabel('AR(1) phi')
    axs[4].set_ylabel('Half-life (days)\nDisplay capped at 1000');axs[4].set_xlabel('Date')
    boundaries(axs,bounds)
    save(fig,directory/(tag+'_diagnostics'))

def overview(directory,panel,quantiles,portfolios,attribution,alarm,bounds):
    directory=Path(directory);setup()
    fig,axs=plt.subplots(2,1,figsize=(12,8),sharex=True)
    for ax,strategy in zip(axs,['static','rolling']):
        palette={'control':'#1f77b4','beta_entry':'#ff7f0e','beta_reduction':'#2ca02c','vol_entry':'#d62728','risk_scaled_control':'#9467bd'}
        for variant in palette:
            f=portfolios.get((strategy,variant))
            if f is not None:
                if variant=='risk_scaled_control':
                    start=pd.Timestamp(bounds['test']['start'])
                    base=portfolios[(strategy,'control')]
                    anchor=(1+base.loc[base.index<start,'net']).prod()
                    shown=f.loc[start:]
                    ax.plot(shown.index,anchor*(1+shown.net).cumprod(),label='risk scaled control (test only)',lw=1.2,color=palette[variant])
                else:
                    ax.plot(f.index,(1+f.net).cumprod(),label=variant.replace('_',' '),lw=1.2,color=palette[variant])
        ax.set_title(strategy.title()+' mean | Out-of-sample portfolio, net of reference costs')
        ax.set_ylabel('Growth of $1');ax.legend(ncol=3,fontsize=8)
    boundaries(axs,bounds);save(fig,directory/'strategy_comparison')
    if not quantiles.empty:
        q=quantiles[(quantiles.window==252)&(quantiles.horizon==20)&(quantiles.outcome=='convergence')&(quantiles.stage=='test')&(quantiles.population=='all_dates')]
        fig,axs=plt.subplots(1,2,figsize=(12,4))
        for ax,strategy in zip(axs,['static','rolling']):
            for feature,g in q[q.strategy==strategy].groupby('feature'):
                ax.plot(g['quantile'],g['mean'],marker='o',label=feature)
            ax.set_title(strategy.title()+' | Holdout, 20-day convergence');ax.set_xlabel('Development-defined quintile');ax.set_ylabel('Fraction of initial deviation removed');ax.legend()
        save(fig,directory/'quantile_convergence')
    selected=panel[(panel.window==252)&(panel.horizon==20)&(panel.strategy=='static')&(panel.stage=='test')]
    if not selected.empty:
        pair=selected.pair.iloc[0];g=selected[selected.pair==pair].set_index('date').sort_index()
        fig,axs=plt.subplots(2,1,figsize=(12,6),sharex=True)
        axs[0].plot(g.index,g.beta_instability,label='252-day beta instability');axs[0].legend();axs[0].set_ylabel('Descriptive units')
        axs[1].plot(g.index,g.convergence.clip(-5,5),lw=.8,label='Subsequent 20-day convergence (outcome)');axs[1].legend();axs[1].set_ylabel('Fraction removed\nDisplay clipped ±5')
        axs[0].set_title(pair+' | Observable indicator and subsequent outcome, final holdout')
        save(fig,directory/'instability_and_forward_convergence')
    a=attribution[(attribution.stage=='test')&(attribution.variant.isin(['beta_entry','beta_reduction','vol_entry']))]
    if not a.empty:
        fig,axs=plt.subplots(2,1,figsize=(12,8))
        for ax,strategy in zip(axs,['static','rolling']):
            table=a[a.strategy==strategy].pivot(index='pair',columns='variant',values='delta_return')
            table.plot.bar(ax=ax);ax.axhline(0,color='black',lw=.6);ax.set_ylabel('Pair cumulative-return difference');ax.set_title(strategy.title()+' | Holdout attribution (compound pair returns)')
        save(fig,directory/'pair_attribution')
    if not alarm.empty:
        a=alarm[(alarm.stage=='test')&(alarm.variant=='beta_entry')]
        fig,axs=plt.subplots(1,2,figsize=(13,5))
        for ax,strategy in zip(axs,['static','rolling']):
            g=a[a.strategy==strategy].set_index('pair')
            g[['flagged_baseline_entries','missed_profitable_recoveries','avoided_losses']].plot.bar(ax=ax)
            ax.set_title(strategy.title()+' | Flagged baseline-entry counterfactuals');ax.set_ylabel('Trades');ax.legend(fontsize=8)
        save(fig,directory/'signals_and_missed_recoveries')
