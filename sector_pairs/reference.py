"""Rounded values transcribed from all three tables of the supplied four-page PDF."""
import pandas as pd

def reference_pairs():
    columns=['pair','eg_stat','p_min','beta','alpha','sigma','oos_adf_stat','oos_adf_p',
             'static_entries','static_return','static_sharpe','rolling_return','rolling_sharpe']
    rows=[
        ['XLU/XLK',-4.19,.004,.708,.644,.081,-2.02,.278,1,-.293,-.35,.179,.30],
        ['XLU/XLI',-3.95,.009,.833,-.415,.086,-2.53,.109,4,.242,.54,.259,.58],
        ['XLB/XLU',-3.87,.011,.866,.535,.093,-3.32,.014,5,.324,.54,.250,.52],
        ['XLV/XLY',-3.58,.026,.891,.860,.080,-2.20,.205,7,.508,.86,.181,.38],
        ['XLB/XLP',-3.50,.032,.725,.378,.105,-3.92,.002,2,-.023,.01,.143,.36],
        ['XLI/XLV',-3.47,.035,.865,.386,.087,-1.01,.748,3,.030,.10,-.047,-.07],
        ['XLU/XLY',-3.35,.048,.654,.488,.104,-2.61,.090,5,.424,.65,.342,.64],
        ['XLB/XLI',-3.22,.067,.753,.064,.068,-2.22,.198,3,.169,.50,-.025,-.05],
        ['XLB/XLV',-3.18,.073,.644,.383,.108,-2.77,.063,3,.119,.23,.202,.44]]
    return pd.DataFrame(rows,columns=columns)

PORTFOLIO={('static','selection'):{'return':.662,'max_drawdown':-.083,'sharpe':.90},
           ('rolling','selection'):{'return':.339,'max_drawdown':-.080,'sharpe':.53},
           ('static','oos'):{'return':.163,'max_drawdown':-.062,'sharpe':.55},
           ('rolling','oos'):{'return':.173,'max_drawdown':-.039,'sharpe':.68}}

def compare_pairs(actual):
    ref=reference_pairs().set_index('pair'); actual=actual.set_index('pair')
    records=[]
    for pair in ref.index:
        for measure in ref.columns:
            a=actual.loc[pair,measure]; r=ref.loc[pair,measure]
            records.append(dict(pair=pair,measure=measure,reference=r,reproduced=a,
                                difference=a-r,absolute_difference=abs(a-r),relative_difference=(a-r)/abs(r) if r else float('nan')))
    return pd.DataFrame(records)
