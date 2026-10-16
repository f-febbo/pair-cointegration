"""Standalone table/figure briefing using the already installed plotting stack."""
import re
import textwrap
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

def export_briefing(directory):
    directory=Path(directory)
    with PdfPages(directory/'research_briefing.pdf') as pdf:
        def footer(fig):
            fig.text(.04,.025,'Sector ETF structural stability | Historical research, not prospective validation',fontsize=8,color='#666666')
        summary=(directory/'executive_summary.md').read_text()
        summary=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',summary).replace('**','').replace('# Executive summary','').strip()
        lines=[]
        for paragraph in summary.split('\n\n'):
            lines.extend(textwrap.wrap(paragraph,width=112));lines.append('')
        for page in range(0,len(lines),32):
            fig=plt.figure(figsize=(11.7,8.3))
            fig.text(.05,.94,'Do structural instability measures predict\nsector ETF relationship breakdown?',fontsize=20,weight='bold',color='#18384d',va='top')
            fig.text(.05,.81,'Executive research briefing' if page==0 else 'Executive briefing, continued',fontsize=12)
            fig.text(.05,.76,'\n'.join(lines[page:page+32]),fontsize=9,linespacing=1.45,va='top')
            footer(fig);pdf.savefig(fig);plt.close(fig)
        def table_page(title,frame,columns,note):
            view=frame[columns].copy()
            for c in view.columns:
                if pd.api.types.is_float_dtype(view[c]):
                    view[c]=view[c].map(lambda v:f'{v:.4f}' if np.isfinite(v) else '—')
            view=view.fillna('—')
            fig,ax=plt.subplots(figsize=(11.7,8.3));ax.axis('off')
            fig.text(.04,.94,title,fontsize=18,weight='bold',color='#18384d')
            names=['\n'.join(textwrap.wrap(c.replace('_',' '),width=15)) for c in view.columns]
            height=min(.76,.10+.045*(len(view)+1))
            t=ax.table(cellText=view.values,colLabels=names,loc='upper left',cellLoc='center',bbox=[0,.84-height,1,height])
            t.auto_set_font_size(False);t.set_fontsize(7.2)
            for (r,c),cell in t.get_celld().items():
                cell.set_edgecolor('#e0e6ea')
                if r==0:cell.set_facecolor('#18384d');cell.set_text_props(color='white',weight='bold')
                elif r%2:cell.set_facecolor('#f1f5f7')
            fig.text(.04,.11,textwrap.fill(note,width=145),fontsize=9,va='top')
            footer(fig);pdf.savefig(fig,bbox_inches='tight');plt.close(fig)
        baseline=pd.read_csv(directory/'baseline_pair_metrics.csv')
        table_page('Historical nine-pair baseline replication',baseline,
                   ['pair','beta','sigma','static_entries','static_completed_trades','static_return','static_sharpe','rolling_return','rolling_sharpe'],
                   'Reference-log convention: normalized log-spread changes compounded as daily returns. Entries include open trades; completed trades are separate. Returns use decimal fractions. Full signed, absolute and relative target differences are in the baseline assessment; exact original-input replication is not certified.')
        pred=pd.read_csv(directory/'predictive_results.csv')
        primary=pred[(pred.primary==True)&(pred.stage=='test')]
        table_page('Primary incremental forecast comparisons | Holdout',primary,
                   ['strategy','feature','n','n_dates','mse_gain','gain_ci_low','gain_ci_high','p_gain','q_primary_gain_holm'],
                   '252-session features, 20-session convergence outcomes. Positive loss gain favors instability. Bootstrap uses 60-session shared-date blocks, conditional on development models. Holm corrects four primary comparisons. Judge expected direction, confidence intervals, multiplicity and the small number of independent blocks together; consult the executive findings for the conclusion.')
        s=pd.read_csv(directory/'strategy_results.csv')
        main=s[(s.stage=='test')&s.variant.isin(['control','beta_entry','beta_reduction','vol_entry','risk_scaled_control'])]
        table_page('Net economic comparison | Final holdout',main,
                   ['strategy','variant','return','sharpe','max_drawdown','volatility','capital_utilization','completed_trades','transaction_costs'],
                   'Simple adjusted leg returns, original scalar-position cost convention. Entry filters preserve existing exits; reduction halves gross exposure. Other pairs receive no compensating capital. Daily leg-rebalancing costs and alternative windows are separately reported. Consult the full Markdown report for assumptions and all negative/insufficient specifications.')
        for path in sorted((directory/'figures').glob('*.png')):
            fig,ax=plt.subplots(figsize=(11.7,8.3));ax.axis('off')
            ax.imshow(plt.imread(path));footer(fig);pdf.savefig(fig,bbox_inches='tight');plt.close(fig)
