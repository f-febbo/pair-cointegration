def specifications():
    return [dict(name=f'{kind}_local_beta_{action}',family='local_calibration',control=kind,
                 action='entry_filter' if action=='entry' else 'reduction',local_quantile_days=252)
            for kind in ('static','rolling') for action in ('entry','reduction')]
