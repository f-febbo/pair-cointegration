"""Adjusted-close acquisition, immutable source snapshot, and calendar audit."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from .config import UNIVERSE

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def download(directory, config):
    import yfinance as yf
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / 'adjusted_close.csv'
    if target.exists():
        raise FileExistsError('Snapshot exists; use a new directory to acquire revised data.')
    cache = directory / 'yahoo_cache'
    cache.mkdir(exist_ok=True)
    yf.set_tz_cache_location(str(cache))
    end_exclusive = str((pd.Timestamp(config.end) + pd.Timedelta(days=1)).date())
    series = []
    for ticker in UNIVERSE:
        frame = yf.download(ticker, start=config.start, end=end_exclusive,
                            auto_adjust=False, actions=True, repair=False,
                            progress=False, threads=False, timeout=30)
        if frame is None or frame.empty:
            raise ValueError(f'No Yahoo data for {ticker}; no substitution is permitted.')
        frame.to_csv(directory / f'{ticker}_raw.csv')
        if 'Adj Close' not in frame.columns:
            raise ValueError(f'{ticker}: adjusted close unavailable')
        adj = frame['Adj Close']
        if isinstance(adj, pd.DataFrame):
            adj = adj.iloc[:, 0]
        adj.index = pd.to_datetime(adj.index).tz_localize(None).normalize()
        series.append(adj.rename(ticker))
    pd.concat(series, axis=1).sort_index().to_csv(target, index_label='Date')
    manifest = {'source':'Yahoo Finance via yfinance; Adj Close, auto_adjust=False, repair=False',
                'retrieved_utc':datetime.now(timezone.utc).isoformat(),
                'requested_start':config.start, 'requested_end_inclusive':config.end,
                'adjustment':'Vendor dividend- and split-adjusted close; retrospective revisions possible.',
                'yfinance_version':yf.__version__, 'sha256':sha256(target),
                'raw_sha256':{p.name:sha256(p) for p in directory.glob('*_raw.csv')}}
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    return target

def load_prices(path, config):
    path = Path(path)
    manifest_path = path.with_name('manifest.json')
    if not manifest_path.exists():
        raise ValueError('A manifest.json declaring source and adjustment is required beside the CSV.')
    manifest = json.loads(manifest_path.read_text())
    for key in ('source', 'adjustment', 'sha256'):
        if not manifest.get(key):
            raise ValueError(f'Manifest missing {key}')
    if manifest['sha256'] != sha256(path):
        raise ValueError('Snapshot SHA256 does not match manifest')
    prices = pd.read_csv(path, index_col=0, parse_dates=True)
    prices.index = pd.DatetimeIndex(prices.index).tz_localize(None)
    if prices.index.has_duplicates or not prices.index.is_monotonic_increasing:
        raise ValueError('Dates must be unique and increasing')
    if set(prices.columns) != set(UNIVERSE):
        raise ValueError('CSV must contain exactly the original eleven ETFs')
    prices = prices.loc[config.start:config.end, list(UNIVERSE)].astype(float)
    if (prices <= 0).any().any() or np.isinf(prices.to_numpy()).any():
        raise ValueError('Nonpositive or infinite price')
    missing = prices.isna().sum().to_dict()
    removed = [str(d.date()) for d in prices.index[prices.isna().any(axis=1)]]
    prices = prices.dropna(how='any')  # intersection, never interpolate or forward-fill
    if len(prices) < 1000:
        raise ValueError('Insufficient observations for this protocol')
    n_is = int(len(prices) * config.split)
    audit = {'manifest':manifest, 'missing_by_asset':missing, 'removed_dates':removed,
             'calendar':'Intersection of observed vendor daily sessions; no filling. All-asset absent dates cannot be detected without an exchange calendar.',
             'observations':len(prices), 'is_observations':n_is, 'oos_observations':len(prices)-n_is,
             'actual_start':str(prices.index[0].date()), 'actual_end':str(prices.index[-1].date()),
             'is_end':str(prices.index[n_is-1].date()), 'oos_start':str(prices.index[n_is].date()),
             'reference_boundaries_match':str(prices.index[n_is-1].date())=='2020-02-26' and str(prices.index[n_is].date())=='2020-02-27',
             'reference_counts_match':len(prices)==5542 and n_is==3879,
             'requested_endpoints_match':str(prices.index[0].date())==config.start and str(prices.index[-1].date())==config.end}
    return prices, n_is, audit

def chronology(index, n_is):
    n_oos = len(index)-n_is
    a, b = n_is + int(.40*n_oos), n_is + int(.70*n_oos)
    labels = pd.Series('selection', index=index)
    labels.iloc[n_is:a] = 'development'
    labels.iloc[a:b] = 'validation'
    labels.iloc[b:] = 'test'
    bounds = {s:{'start':str(labels[labels==s].index[0].date()),
                 'end':str(labels[labels==s].index[-1].date()), 'n':int((labels==s).sum())}
              for s in labels.unique()}
    return labels, bounds
