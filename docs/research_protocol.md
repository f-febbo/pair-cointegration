# Research protocol and fixed evaluation choices

Consolidated October 16, 2026 during implementation after an initial execution. The windows, horizons, predictors and trading thresholds were encoded before the first extension run; this document is not an independent preregistration. Subsequent changes corrected trade-label cost timing, handled unidentified nuisance regressors, and preserved missing-session gaps in inference. The directional interpretation rule was made explicit during review. No window, threshold or feature was selected using holdout performance. The historical reference and its chosen universe are already known; this is a chronological retrospective holdout, not a pristine prospective experiment.

## Data and reference replication

- Eleven original ETFs, adjusted daily closes, September 29, 2004–October 8, 2026.
- Retain the first 70% for pair selection. Both orientations, min p<0.10, no FDR change to the strategy universe. Report orientation-corrected BH and BY separately.
- Baseline evaluates the nine historical orientations and reproduced-selection portfolio separately.
- Reconciliation of all rounded report returns identifies compounded gross-normalized log-spread increments as the reference convention. Report these for replication; simple leg returns are the primary economic extension convention. Entry count matches reference trade counts; completed trades and open trades are separately disclosed.

## Chronology

| Stage | Dates | Purpose |
|---|---|---|
| Selection | 2004-09-29–2020-02-26 | Original pair selection and frozen OLS |
| Development | 2020-02-27–2022-10-14 | Forecast fits, scaling, quantiles and thresholds |
| Validation | 2022-10-17–2024-10-10 | Unchanged specification evaluation; risk-scale comparator calibration |
| Test | 2024-10-11–2026-10-08 | Final chronological evaluation |

Purge forward labels crossing each stage end, at the outcome's own horizon. No test use in threshold calibration or forecast fitting. Price-level OLS and AR standard errors are descriptive. Their conventional break-test critical values are not used.

## Confirmatory family

Four tests: static/rolling equilibrium × beta-instability/phi predictor. Window=252 sessions, horizon=20 sessions, population=all evaluable dates, outcome=fractional convergence. Higher instability or persistence should mean lower convergence. Baseline features: absolute z, recent spread volatility, signed recent spread change, matured trailing 20-day convergence and pair intercepts. Extended model adds one indicator. Models are fitted in development, including clipping limits and scale parameters. Compare date-averaged squared prediction losses; use Holm across the four tests. A claim supporting deterioration requires positive incremental loss improvement, Holm p<0.05, positive moving-date block-bootstrap lower limit, and negative convergence association in both development and test.

Inference: shared-date cross-section aggregation, HAC with at least 60 sessions, circular moving-date bootstrap with 60-session blocks and 499 replications, seed 20261015. Bootstrap intervals condition on development fits. Report small effective block counts and assumption limits. Missing calendar sessions in complete-case inference are retained as gaps rather than compressed into consecutive observed days.

## Exploratory analysis, retained regardless of sign

126/504-day windows; 5/60-day horizons; convergence hit, capped first-hit time, adverse excursion, hypothetical trade mark-out, actual-entry population, existing-position continuation and future-only AR estimates. Binary forecasts use clipped linear probability models and Brier scores. Correct all estimable exploratory test families with BY; report rank associations descriptively. Quantiles use development cutpoints. Preserve insufficient-sample results.

Fractional convergence fixes equilibrium at t and omits denominators below 0.05 sigma. Hits use 0.25 sigma. Future trade mark-outs include entry/exit costs; positions unresolved at the horizon are closed for labeling and flagged as censored. Existing-position continuation respects the actual held direction and excludes sunk entry costs.

## Trading, with unchanged original thresholds

Primary detector: 252-day |beta_t−beta_IS|/descriptive SE(beta_t). Pair-specific 90th development percentile. Entry suspension leaves existing positions alone; reduction halves gross exposure while high. No reallocation. Volatility filter at its own 90th percentile is the competing rule. Deploy after development. No threshold search. Keep original ±1.5 entry and |z|≤0.25 exit.

Sensitivity variants: 126/504 beta entry filters, phi252 entry filter, calendar-three-year mean, IS boundary carry, reference-log control, and simple-leg control/primary modifications with full daily leg turnover charged. Validation-utilization-scaled control is fixed before test. Compare validation/test, return, Sharpe, drawdown, volatility, utilization, counts, turnover, costs, shadow suppressed entries, unresolved counterfactuals, and missed profitable recoveries.

No HMM, regime clustering, ML ensemble, Kalman trading, threshold optimization, Johansen baskets or SPY optimization.
