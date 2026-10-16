import numpy as np
import pandas as pd

def metrics(frame):
    r=frame['net'].fillna(0)
    wealth=(1+r).cumprod()
    peaks=wealth.cummax().clip(lower=1.)
    sd=r.std(ddof=1)
    out={'return':wealth.iloc[-1]-1, 'sharpe':np.sqrt(252)*r.mean()/sd if sd>0 else np.nan,
         'max_drawdown':(wealth/peaks-1).min(), 'volatility':sd*np.sqrt(252)}
    for col,name in [('exposure','capital_utilization'),('turnover','turnover'),('cost','transaction_costs')]:
        if col in frame:
            out[name]=frame[col].mean() if col=='exposure' else frame[col].sum()
    return out

def portfolio(frames):
    cols=['net','gross','cost','exposure','turnover']
    return pd.concat([f[cols] for f in frames], keys=range(len(frames))).groupby(level=1).mean()
