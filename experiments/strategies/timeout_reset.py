def specifications():
    return [dict(name=f'{kind}_timeout_{cap}_reset',family='timeout_reset',control=kind,
                 max_holding=cap,reset_after_timeout=True)
            for kind in ('static','rolling') for cap in (60,120)]
