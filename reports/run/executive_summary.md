# Executive summary

This reproducible study uses the original eleven ETFs and the reference's historical nine pairs. Its 5542 daily observations reproduce the reported sample dates and 70/30 boundaries. See [baseline replication](baseline_replication.md) for selection and numerical discrepancies; exact original-input replication is not claimed.

**Can instability be measured?** Yes, trailing OLS coefficient departures, residual dispersion, AR persistence and valid monotonic half-lives can be measured using only observed history. These are descriptive indicators, not validated declarations of discrete market regimes.

**Does instability predict deterioration, and add to simple predictors?** 0 of 4 designated primary comparisons show positive forecast-loss improvement with Holm p<0.05, a positive block-bootstrap lower confidence limit, and the expected negative convergence association in development and holdout. The primary analysis does not establish credible incremental predictive value. Detectable historical instability alone is insufficient evidence of useful forecasting or trading gains. The baseline forecast already includes spread magnitude, recent volatility, recent spread changes and matured convergence. Statistical associations alone are not evidence of useful incremental forecasting.

Exploratory results are mixed: 2 BY-adjusted comparisons favor the extended forecast, while 32 favor the simpler baseline. The rolling 504-day beta_instability / 20-day future-phi improvement is exploratory evidence for persistence forecasting, requiring prospective replication and economic validation. The static 504-day beta_instability / 60-day convergence improvement has greater convergence at higher indicator values, contrary to the proposed deterioration direction. These exploratory findings do not overturn the primary result.

**Are results credible?** The design separates development, validation and test, purges crossing labels, groups dependence by shared dates, and adjusts for multiplicity. Nevertheless, the final sample has few independent 60-day blocks, rare entries and possible longer persistence. Treat results as conditional historical evidence requiring prospective replication.

**Does acting on instability improve performance?** Final-holdout comparisons:

- static/beta_entry: net return 2.00% versus 2.00%, Sharpe 0.258 versus 0.258, utilization 70.2% versus 70.2%
- static/beta_reduction: net return 1.72% versus 2.00%, Sharpe 0.233 versus 0.258, utilization 67.9% versus 70.2%
- static/vol_entry: net return 2.00% versus 2.00%, Sharpe 0.258 versus 0.258, utilization 70.2% versus 70.2%
- rolling/beta_entry: net return 1.62% versus 1.56%, Sharpe 0.328 versus 0.312, utilization 40.3% versus 42.1%
- rolling/beta_reduction: net return 1.43% versus 1.56%, Sharpe 0.296 versus 0.312, utilization 40.2% versus 42.1%
- rolling/vol_entry: net return 1.56% versus 1.56%, Sharpe 0.312 versus 0.312, utilization 42.1% versus 42.1%

Changes must also be compared with volatility filtering and the validation-scaled control. Lower capital utilization can reduce drawdowns without adding information. Costs from exposure changes are included; daily rebalancing cost sensitivities are in the full report.

**How sensitive are conclusions?** Across 36 holdout convergence specifications, date-weighted loss gains range from -0.0824 to 0.2173. At full-family BY 5%, 1 favor the extended forecast and 5 favor the simpler baseline. Validation and test agree on the sign of loss improvement in 26 of 36 specifications. These are exploratory robustness counts, not independent confirmations. Calendar-three-year mean, boundary carry and executable turnover costs are also reported. No best threshold or specification is selected. Negative and insufficient-sample results remain in `predictive_results.csv`.

Read [the research report](research_report.md) for tables, figures and explicit limits.
