from itertools import combinations
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint, adfuller
from statsmodels.stats.multitest import multipletests
from .config import UNIVERSE, REFERENCE_PAIRS

def select_pairs(prices, n_is):
    logs = np.log(prices.iloc[:n_is])
    records = []
    for first, second in combinations(UNIVERSE, 2):
        t1, p1, _ = coint(logs[first], logs[second], trend='c', autolag='aic')
        t2, p2, _ = coint(logs[second], logs[first], trend='c', autolag='aic')
        y, x, stat, p = (first,second,t1,p1) if p1<=p2 else (second,first,t2,p2)
        fit = sm.OLS(logs[y], sm.add_constant(logs[x])).fit()
        records.append(dict(first=first, second=second, p_first_on_second=p1,
                            p_second_on_first=p2, y=y, x=x, pair=f'{y}/{x}',
                            eg_stat=stat, p_min=p, alpha=fit.params.iloc[0],
                            beta=fit.params.iloc[1], sigma=fit.resid.std(ddof=1),
                            mu=fit.resid.mean(), selected=p<.10))
    table = pd.DataFrame(records)
    table['p_orientation_bonferroni'] = np.minimum(1, 2*table.p_min)
    table['q_bh_naive_min'] = multipletests(table.p_min, method='fdr_bh')[1]
    table['q_bh_orientation_corrected'] = multipletests(table.p_orientation_bonferroni, method='fdr_bh')[1]
    table['q_by_orientation_corrected'] = multipletests(table.p_orientation_bonferroni, method='fdr_by')[1]
    # BY is also supplied because pairs share ETF exposures.
    return table.sort_values('p_min').reset_index(drop=True)

def models_for_reference(prices, n_is, selection):
    """Fit historical nine independently of reproduced selection, visibly labeled."""
    records=[]
    logs=np.log(prices)
    for y,x in REFERENCE_PAIRS:
        fit=sm.OLS(logs[y].iloc[:n_is], sm.add_constant(logs[x].iloc[:n_is])).fit()
        t,p,_=coint(logs[y].iloc[:n_is], logs[x].iloc[:n_is], trend='c', autolag='aic')
        row=selection[(selection['first'].isin([y,x])) & (selection['second'].isin([y,x]))].iloc[0]
        records.append(dict(pair=f'{y}/{x}',y=y,x=x,alpha=fit.params.iloc[0],beta=fit.params.iloc[1],
                            sigma=fit.resid.std(ddof=1),mu=fit.resid.mean(),eg_stat=t,p_min=p,
                            reproduced_selected=bool(row.selected),winning_orientation=row.pair))
    return pd.DataFrame(records)

def spread(prices, model):
    return np.log(prices[model['y']])-model['alpha']-model['beta']*np.log(prices[model['x']])

def frozen_oos_adf(s, n_is):
    t,p,*_=adfuller(s.iloc[n_is:], regression='c', autolag='AIC')
    return {'oos_adf_stat':t,'oos_adf_p':p}
