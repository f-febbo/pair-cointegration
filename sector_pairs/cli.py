import argparse
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',str(Path.cwd()/'.mplconfig'))
from .config import Config

def main():
    parser=argparse.ArgumentParser(description='Sector ETF structural stability research')
    parser.add_argument('command',choices=['download','baseline','run','evaluate','figures','report'])
    parser.add_argument('--data',default='data/yahoo_20261016/adjusted_close.csv')
    parser.add_argument('--output',default='reports/run')
    parser.add_argument('--bootstrap-reps',type=int,default=499)
    args=parser.parse_args();config=Config(bootstrap_reps=args.bootstrap_reps)
    if args.command=='download':
        from .data import download
        print(download(Path(args.data).parent,config));return
    if args.command in ('baseline','run'):
        from .pipeline import baseline,research
        (baseline if args.command=='baseline' else research)(args.data,args.output,config);return
    import json
    import pandas as pd
    out=Path(args.output)
    if args.command=='evaluate':
        from .evaluation import evaluate
        panel=pd.read_csv(out/'predictive_panel.csv.gz',parse_dates=['date','label_end'])
        r,q,f=evaluate(panel,config)
        r.to_csv(out/'predictive_results.csv',index=False);q.to_csv(out/'quantile_results.csv',index=False);f.to_csv(out/'primary_forecasts.csv',index=False)
    elif args.command=='report':
        from .reporting import research_report
        research_report(out,json.loads((out/'data_audit.json').read_text()),json.loads((out/'chronology.json').read_text()),pd.read_csv(out/'predictive_results.csv'),pd.read_csv(out/'strategy_results.csv'),pd.read_csv(out/'signal_analysis.csv'),config)
    else:
        from .figures import overview
        panel=pd.read_csv(out/'predictive_panel.csv.gz',parse_dates=['date','label_end'])
        portfolios={}
        for path in out.glob('*_portfolio.csv'):
            kind,variant=path.stem.removesuffix('_portfolio').split('_',1)
            if kind in ('static','rolling'):portfolios[(kind,variant)]=pd.read_csv(path,index_col=0,parse_dates=True)
        overview(out/'figures',panel,pd.read_csv(out/'quantile_results.csv'),portfolios,pd.read_csv(out/'pair_attribution.csv'),pd.read_csv(out/'signal_analysis.csv'),json.loads((out/'chronology.json').read_text()))

if __name__=='__main__':main()
