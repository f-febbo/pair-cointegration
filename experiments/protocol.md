# Exploratory iteration protocol

Fixed before executing this batch, October 16, 2026. The previous final period has already been examined. All further results through October 8, 2026 are exploratory; a better backtest cannot rescue an independent confirmatory claim. Every evaluated specification and unsuccessful outcome is retained. No repeat-until-significant rule is used.

Original eleven assets, historical nine pairs, frozen original IS model, 70/30 boundary and ±1.5 / 0.25 signal thresholds remain unchanged. Reference replication and previous reports are preserved. New comparisons use simple adjusted leg returns and charge five basis points on actual daily leg turnover, including weight restoration and exposure changes. A ten-basis-point cost stress is reported for every variant.

## Fixed candidate families

1. **Local instability calibration:** replace the original COVID-era fixed development threshold with the trailing 252-session 90th percentile, excluding today's observation and requiring 126 prior valid readings. The underlying indicator stays 252-day beta instability. Compare entry suspension and half-exposure reduction, for both static and three-year rolling controls.
2. **Shorter equilibrium memory:** use a trailing 252- or 126-session spread mean, retaining the original frozen hedge ratio and IS sigma. Compare against the original 756-session rolling-mean control. This changes equilibrium estimation, not the entry/exit thresholds; it is a separate strategy extension.
3. **Time-out and reset:** exit a position after 60 or 120 held sessions if the original exit has not occurred. Following a time-out, prohibit reentry until the spread first returns inside |z|≤0.25. Compare both static and rolling controls. This deliberately adds an exit rule as a new risk-control strategy, rather than retroactively changing reference replication.

There are ten candidates: four local-calibration, two shorter-equilibrium and four time-out/reset combinations. Thresholds, windows and holding caps will not be optimized after results. All variants follow the original strategy for the first 252 OOS sessions and deploy afterward, preserving then-open positions. Caps may close an old position at deployment; its age is already known. No future price is consulted. Local thresholds use only prior observed history.

## Evaluation and what counts as positive

The original development/validation/test date boundaries are retained. Validation is the candidate nomination period; rank its candidates by net Sharpe improvement over the appropriate unmodified control, requiring a positive net-return difference. Prefer a positive result that also survives cost stress and does not materially increase drawdown. Test-period checks are explicitly retrospective, with all candidates reported.

Report net return, Sharpe, volatility, drawdown, utilization, costs, turnover, completed trades, entry counts and time-outs. Compare the modified strategy with a control scaled by the variant/control capital-utilization ratio observed before the evaluation period. Risk scaling is fixed before validation and before retrospective test, never fit to that period's realized returns or volatility. It is a capital-use comparison, not exact volatility matching.

For all ten candidates, evaluate paired date-level net-return differences versus control with 60-session HAC and shared-date moving-block bootstrap. Apply Holm correction across all ten validation comparisons, and separately across all ten retrospective test comparisons. Economic improvement and statistical evidence are reported separately. This family correction does not erase prior experimentation or make the viewed historical test independent.

Walk-forward robustness uses 252-session blocks after the initial 252-session OOS calibration, cutting a block at the original test boundary. No fold is silently discarded. Also report fixed ten-basis-point trading costs. Variants are deterministic history-only rules, so folds do not choose new parameters.

A candidate nominated from validation may be frozen for future paper evaluation beginning October 19, 2026, the next Monday. That future evaluation is the appropriate place for an independent claim. No live orders, future data fabrication, or profit guarantee is part of this research.
