def specifications():
    return [dict(name=f'rolling_mean_{window}',family='equilibrium',control='rolling',mean_days=window)
            for window in (126,252)]
