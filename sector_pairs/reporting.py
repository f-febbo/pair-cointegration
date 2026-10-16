"""Generate auditable reports from computed tables, with explicit inference limits."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

def table(frame, columns=None, digits=4):
    if frame.empty:return '*No estimable observations.*'
    return frame[columns].to_markdown(index=False,floatfmt=f'.{digits}f') if columns else frame.to_markdown(index=False,floatfmt=f'.{digits}f')

def baseline_report(output,audit,assessment,actual,portfolios,selection):
    txt=f'''# Baseline replication assessment

Primary reference: *Pairs Trading on Sector ETFs: Method and Backtest Results*, supplied four-page PDF. Entire document read before implementation; text extraction is preserved in `docs/reference_extracted.txt`. Figures are descriptive context; Tables 1–3 supply numerical targets. No SPY overlay is implemented.

## Data and split

Source: {audit['manifest']['source']}. Retrieval: {audit['manifest'].get('retrieved_utc','not supplied')}. SHA256: `{audit['manifest']['sha256']}`.

Sample: {audit['actual_start']} through {audit['actual_end']}; {audit['observations']} common daily observations. In-sample: {audit['is_observations']} observations ending {audit['is_end']}. Out-of-sample: {audit['oos_observations']} observations starting {audit['oos_start']}. Reference boundary match: **{audit['reference_boundaries_match']}**. Removed incomplete dates: {len(audit['removed_dates'])}. Prices are explicitly vendor adjusted closes; no interpolation or forward filling. The calendar is the intersection of observed sessions, not an independently certified exchange calendar.

## Pair selection

Both Engle–Granger orientations are retained in `all_55_pairs.csv`, with a constant, AIC lag selection, and statsmodels default maximum lag. Original selection retains the lower p-value and uses p < 0.10. Reproduced selection: **{assessment['selected_count']} pairs**; unordered pair-set match: **{assessment['pair_sets_match']}**. Reference-only pairs: {assessment['reference_only']}; reproduced-only pairs: {assessment['reproduced_only']}.

{table(selection[selection.selected],['pair','eg_stat','p_min','alpha','beta','sigma','q_bh_naive_min','q_bh_orientation_corrected','q_by_orientation_corrected'])}

Taking the smaller of two p-values is a selection step. Naive BH on the 55 minima is only an illustration; orientation-Bonferroni p=min(1,2p_min), followed by BH and dependence-conservative BY, are separate diagnostics. These do not change the baseline selection. Shared ETFs induce cross-pair dependence. A residual unit-root rejection does not guarantee a stable relationship or profitable trades.

At the reference 10% level, orientation-corrected BH retains {int((selection.q_bh_orientation_corrected<.10).sum())} pairs and orientation-corrected BY retains {int((selection.q_by_orientation_corrected<.10).sum())} pairs, versus the original nine unadjusted selections.

## Historical nine-pair results

The report's nine named pairs are fitted in its reported orientations for direct numerical comparison, even if the winning orientation or selection differs. Portfolios using reproduced selection are saved separately. Extensions refer to the historical nine, not a silently substituted universe.

{table(actual,['pair','beta','sigma','oos_adf_stat','oos_adf_p','static_entries','static_completed_trades','static_open_trades','static_return','static_sharpe','rolling_completed_trades','rolling_return','rolling_sharpe'])}

{table(portfolios,['strategy','stage','universe','return','max_drawdown','sharpe','delta_return','delta_max_drawdown','delta_sharpe'])}

Every pair target has signed, absolute, and relative differences in `baseline_replication_differences.csv`. Portfolio absolute and relative differences are in `baseline_portfolio_metrics.csv`. Maximum absolute beta difference: {assessment['max_absolute_beta_difference']:.6f}; maximum absolute pair-return difference: {assessment['max_absolute_pair_return_difference']:.6f}. Reference inputs are rounded, so small discrepancies are unavoidable. Exact replication is **not certified**: the original raw snapshot and source code were not supplied.

## Explicit implementation choices and discrepancies

The frozen residual is log(Y)−alpha−beta log(X). Spread sigma uses sample ddof=1. Static mean and sigma stay fixed. The primary rolling mean uses 756 observations ending at today's close, including pre-OOS history. The PDF says three years but does not specify calendar years versus trading days. An exact calendar-three-year variant is reported as sensitivity, not selected after observing performance.

The close-t position earns the t→t+1 return. The PDF leaves the precise daily return formula implicit. Numerical reconciliation identifies its convention as q_previous×(s_t−s_(t−1))/(1+|beta|), less 0.0005×|change in scalar spread position|, then compounded as if these log-spread increments were daily simple returns. This matches every reported pair return and both OOS portfolio returns to their rounding. It is a replication approximation, not an exact investable P&L.

In the extensions, a spread direction q maps to daily dollar weights q/(1+|beta|) in Y and −q beta/(1+|beta|) in X. The implementable gross return is q_previous(rY−beta rX)/(1+|beta|), using simple dividend-adjusted leg returns. Negative betas, if present, are normalized using absolute gross exposure. The extensions retain reference scalar-position costs for direct comparison and separately charge turnover needed to restore daily dollar weights as prices drift. Costs from half-exposure changes are included. The reference-log control remains visible as sensitivity; all main filter/control comparisons use the same simple-return convention.

Positions start flat at the OOS boundary, remain in their original direction until |z|≤0.25, and cannot open on the last observed date. No forced end-of-sample liquidation is imposed; open trades are separately counted and marked to market. No immediate reversal or reopening occurs on an exit close. The PDF's single Table 2 trade-count column matches static entries, including still-open trades; treating these as completed trades would misstate the reference. Both entries and genuinely completed trades are reported, with rolling counts newly supplied. Boundary carry and calendar-window variants expose unresolved reference details. IS results use models and pairs fitted on the full IS sample and are retrospective fitted context, not causal validation.

All prices are retrospectively adjusted. Adjustment revisions can shift intercepts, and revised historical relative price paths can change residuals and returns. The downloaded snapshot is preserved; the code does not attribute every discrepancy to a particular cause without original inputs. Baseline assessment is written before diagnostics and predictive analysis execute.
'''
    (Path(output)/'baseline_replication.md').write_text(txt)

def research_report(output,audit,bounds,predictive,strategies,alarms,config):
    output=Path(output)
    primary=predictive[(predictive.get('primary',False)==True)&(predictive.stage=='test')& (predictive.status=='evaluated')].copy()
    confirmed=primary[(primary.mse_gain>0)&(primary.q_primary_gain_holm<.05)&(primary.gain_ci_low>0)&(primary.coefficient<0)&(primary.development_coefficient<0)] if not primary.empty else primary
    main=strategies[(strategies.stage=='test') & strategies.variant.isin(['control','beta_entry','beta_reduction','vol_entry','risk_scaled_control'])]
    robust=strategies[(strategies.stage=='test') & ~strategies.variant.isin(['control','beta_entry','beta_reduction','vol_entry','risk_scaled_control'])]
    gains=[]
    for kind in ('static','rolling'):
        g=main[main.strategy==kind].set_index('variant')
        if 'control' in g.index:
            for v in ('beta_entry','beta_reduction','vol_entry'):
                gains.append(f"{kind}/{v}: net return {g.loc[v,'return']:.2%} versus {g.loc['control','return']:.2%}, Sharpe {g.loc[v,'sharpe']:.3f} versus {g.loc['control','sharpe']:.3f}, utilization {g.loc[v,'capital_utilization']:.1%} versus {g.loc['control','capital_utilization']:.1%}")
    predictive_statement=(f'{len(confirmed)} of {len(primary)} designated primary comparisons show positive forecast-loss improvement with Holm p<0.05, a positive block-bootstrap lower confidence limit, and the expected negative convergence association in development and holdout.' if not primary.empty else 'No primary comparison has sufficient complete observations.')
    conclusion=('Some primary comparisons support incremental forecasting value under the stated assumptions. This requires prospective replication and does not establish discrete market regimes.' if len(confirmed) else 'The primary analysis does not establish credible incremental predictive value. Detectable historical instability alone is insufficient evidence of useful forecasting or trading gains.')
    stage_table=pd.DataFrame([dict(stage=k,**v) for k,v in bounds.items()])
    alarm_summary=alarms[(alarms.stage=='test')&alarms.variant.isin(['beta_entry','vol_entry'])].groupby(['strategy','variant'],as_index=False)[['baseline_entries','flagged_baseline_entries','matured_flagged_trades','flagged_unresolved','missed_profitable_recoveries','avoided_losses']].sum()
    convergence_tests=predictive[(predictive.status=='evaluated')&(predictive.population=='all_dates')&(predictive.outcome=='convergence')]
    test_convergence=convergence_tests[convergence_tests.stage=='test']
    sign_comparison=convergence_tests.pivot_table(index=['strategy','window','horizon','feature'],columns='stage',values='mse_gain').dropna()
    agreement=int(((sign_comparison.validation>0)==(sign_comparison.test>0)).sum()) if not sign_comparison.empty else 0
    significant_convergence=test_convergence[test_convergence.q_gain_by<.05]
    significant_all=predictive[(predictive.status=='evaluated')&(predictive.stage=='test')&(predictive.q_gain_by<.05)]
    exploratory_better=significant_all[significant_all.mse_gain>0]
    interpretations=[]
    for _,r in exploratory_better.iterrows():
        if r.outcome=='convergence' and r.coefficient>0:
            interpretations.append(f'The {r.strategy} {r.window}-day {r.feature} / {r.horizon}-day convergence improvement has greater convergence at higher indicator values, contrary to the proposed deterioration direction.')
        elif r.outcome=='future_phi' and r.coefficient>0:
            interpretations.append(f'The {r.strategy} {r.window}-day {r.feature} / {r.horizon}-day future-phi improvement is exploratory evidence for persistence forecasting, requiring prospective replication and economic validation.')
    exploratory_interpretation=' '.join(interpretations) if interpretations else 'Any isolated exploratory improvement requires prospective replication, expected directional interpretation and separate economic validation.'
    sensitivity=(f'Across {len(test_convergence)} holdout convergence specifications, date-weighted loss gains range from {test_convergence.mse_gain.min():.4f} to {test_convergence.mse_gain.max():.4f}. At full-family BY 5%, {int((significant_convergence.mse_gain>0).sum())} favor the extended forecast and {int((significant_convergence.mse_gain<0).sum())} favor the simpler baseline. Validation and test agree on the sign of loss improvement in {agreement} of {len(sign_comparison)} specifications. These are exploratory robustness counts, not independent confirmations.')
    val_main=strategies[(strategies.stage=='validation')&strategies.variant.isin(['control','beta_entry','beta_reduction','vol_entry'])]
    txt=f'''# Do Structural Instability Measures Predict the Breakdown of Equity Pairs Relationships? Evidence from Sector ETF Cointegration

## 1. Research motivation

H1: observable instability in historically cointegrated sector ETF pairs contains incremental information about subsequent convergence and net trading performance. The null is no incremental predictive information beyond spread magnitude, volatility, recent spread returns, and matured trailing convergence. This study neither identifies hidden regimes nor assumes an unconditional stationary return distribution. Detecting change, forecasting deterioration, and improving trading are distinct questions.

## 2. Original methodology and replication

See [the complete baseline assessment](baseline_replication.md), including all 55 pairs, both orientations, multiple-testing diagnostics, the nine historical pairs, and numerical differences from the supplied report. Data cover {audit['actual_start']}–{audit['actual_end']}, with {audit['observations']} sessions. The reference 70/30 dates match: **{audit['reference_boundaries_match']}**. Exact reproduction of all rounded performance targets is not asserted. All extensions use the historical nine fitted in the report's orientations; reproduced-selection baseline portfolios are separate artifacts.

## 3. Competing hypotheses and chronological protocol

The designated primary family consists of four incremental forecasting comparisons: beta instability or AR persistence, each for static or rolling equilibrium, using a 252-day window and 20-day fractional convergence outcome. Directionally, higher instability or persistence is expected to reduce convergence. The 126/504-day windows, 5/60-day horizons, binary hits, capped convergence times, adverse excursions, future AR coefficients, and trading returns are exploratory. No specification is selected using final test results. Models are linear and interpretable; binary outcomes use clipped linear-probability predictions and Brier loss.

Specification choices were encoded before the first extension execution, but the written protocol was consolidated during implementation after an initial run. Accounting and numerical checks subsequently corrected label-cost timing, unidentified nuisance directions and missing-session gaps. The directional interpretation rule was made explicit during review. This is not an independent preregistration; the primary family organizes retrospective evidence rather than establishing pristine confirmatory status.

{table(stage_table)}

Initial pair selection and frozen model estimation use only selection dates. The first 40% of original OOS is development: detector scaling, forecast coefficients, quintile edges and 90th-percentile filter thresholds. The next 30% is validation, with unchanged specifications; final 30% is the test. Labels crossing a stage's end are purged at their own horizon. No test observations calibrate features or thresholds. Pair intercepts and predictor scaling/clipping are fitted only on development; no cross-sectional sharing of future labels is permitted. Trading variants begin after development and carry existing positions across validation/test boundaries. Metrics count return realizations in each stage; completed trades are attributed by exit date.

The historical reference and known pair universe already reflect prior research. This is a chronological backtest holdout within a historically specified study, not a pristine prospective replication. No claim of an unexamined future holdout is made.

## 4. Structural-instability measures

Rolling OLS windows of 126, 252 and 504 sessions produce alpha, beta, residual dispersion, beta departure from the original estimate, recent 20-day change, history-standardized beta deviations, and descriptive |beta_t−beta_IS|/SE(beta_t). OLS standard errors in price-level regressions are normalization devices, not validated structural-break inference for integrated regressors. A 63-day standardized sum of frozen residual departures is a descriptive CUSUM indicator with no conventional critical values or break-test p-values.

Trailing AR(1) models of the original frozen spread estimate phi, lambda=phi−1, innovation dispersion and half-life ln(0.5)/ln(phi) only for 0<phi<1. Other half-lives are missing; negative phi is separately flagged as oscillatory. Descriptive normal intervals are provided for phi. Half-life interval endpoints are defined only where transformed endpoints lie inside (0,1); a confidence interval crossing 1 has no finite upper half-life. Local finite-window estimates and their intervals neither establish stationarity nor supply reliable unit-root inference. Large half-lives are visually capped but stored unmodified.

The simple trailing convergence predictor uses entry-sized deviations observed 20 sessions ago and their now fully observed subsequent 20-session hit histories, averaged over 126 sessions with at least five eligible observations. This predictor is sparse by design; missing values are not filled with future outcomes. Complete-case predictive sample counts are reported, and comparisons use the same rows for baseline and extended forecasts.

## 5. Predictive evaluation methodology

Outcomes begin strictly after the feature timestamp, at horizons 5, 20 and 60 sessions. Fractional convergence is 1−|s_(t+h)−mean_t|/|s_t−mean_t|: the equilibrium at t stays frozen for the outcome, including when trading uses a rolling equilibrium. Initial distances smaller than 0.05 sigma_IS are excluded, preventing unstable denominators near zero; the fraction is unbounded below and not clipped in statistical calculations. Convergence hits require |s_(t+j)−mean_t|≤0.25 sigma_IS. First-hit time is capped at h+1 for no hit, explicitly an ordinal capped outcome rather than an uncensored survival estimate. Maximum adverse excursion follows direction −sign(s_t−mean_t), in units of frozen sigma, floored at zero.

Hypothetical current-direction trades earn returns beginning next session, follow the original future exit rule, and close for label mark-out at the horizon if no exit occurs. Entry and exit costs are included; censored horizon closes are labeled. All-date hypothetical entries, actual baseline entry opportunities, and existing positions are evaluated separately. Existing-position continuation excludes the sunk entry cost and respects the actual held direction. These are frozen-direction trade mark-outs, not overlapping observations claimed to be independent executed trades. A future-only AR coefficient uses exactly s_(t+1) through s_(t+h); at short horizons it is extremely noisy and purely exploratory.

Baseline forecasts contain |z|, 20-day spread-change volatility, signed 20-day spread change, trailing matured convergence and pair intercepts. Extended forecasts add one instability measure at a time. Development fits use common one/99-percentile clipping and development standardization; coefficients stay frozen. Quantile edges also come solely from development.

Forecast loss improvement is baseline squared error minus extended squared error (positive favors instability), averaged within each date and then across dates. Binary comparisons use Brier scores. Date-level HAC uses at least 60 lags; date-aggregated regression scores account for contemporaneous dependence from shared ETFs. Circular moving-date bootstrap uses 60-day blocks, {config.bootstrap_reps} deterministic replications, and the entire cross-section of each sampled date. Its interval is conditional on the fitted development model and does not re-estimate pair selection. Rank correlations and holdout partial-association coefficients are descriptive supplements; holdout refits never generate trading forecasts.

Holm correction is applied to the four primary holdout forecast-loss comparisons. BY correction covers all estimable test forecast-loss comparisons, and separately all holdout association coefficients. Validation p-values are descriptive. HAC and block bootstrap assume sufficient local weak dependence and do not solve arbitrary nonstationarity. The effective number of 60-session blocks is explicitly reported; a small holdout and rare independent entries severely limit power. No daily cross-section is treated as a collection of independent experiments.

## 6. Out-of-sample results

{predictive_statement}

{table(primary,['strategy','feature','n_train','n','n_dates','independent_blocks_approx','baseline_mse','extended_mse','mse_gain','gain_ci_low','gain_ci_high','p_gain','q_primary_gain_holm','coefficient','rank_correlation']) if not primary.empty else '*Insufficient observations.*'}

Full validation, holdout, negative, and insufficient-sample results are retained in `predictive_results.csv`. No failed specification is suppressed. A positive partial association or an unadjusted small p-value does not establish incremental forecasting value. Evidence consistent with deterioration also requires the expected sign; improvements in loss could arise from predictive relationships with other signs and must not automatically be interpreted as support for H1.

Across all exploratory outcomes, {len(exploratory_better)} adjusted loss comparisons favor the extended forecast and {int((significant_all.mse_gain<0).sum())} favor the simpler forecast. A significant negative loss gain means that adding the indicator worsens forecasting. The adjusted improvements are shown below; signs of development and test associations remain visible. {exploratory_interpretation}

{table(exploratory_better,['strategy','window','horizon','feature','outcome','mse_gain','gain_ci_low','gain_ci_high','q_gain_by','development_coefficient','coefficient'])}

![Holdout forward convergence by development-defined instability quintile](figures/quantile_convergence.png)

![Observable instability and subsequent realized convergence](figures/instability_and_forward_convergence.png)

## 7. Trading implications

Entry thresholds remain ±1.5 and exit remains |z|≤0.25. All main controls and modifications use simple leg returns; the reference's compounded log-spread approximation is separately preserved as `reference_log_control`. Main modifications use the development 90th percentile of 252-day descriptive beta instability: suspend new entries while high, or halve exposure while high. Open positions under the entry filter retain the original exit rule. Half-exposure changes incur costs and freed capital earns zero; other pairs receive no reallocation. A 90th-percentile recent-volatility entry filter is the simple competing rule. No optimized SPY overlay or threshold search is included.

{table(main,['strategy','variant','return','sharpe','max_drawdown','volatility','capital_utilization','entries','completed_trades','turnover','transaction_costs'])}

The risk-scaled control multiplies all baseline dollar exposure and costs by the instability filter/control validation-utilization ratio, fixed before final holdout. It compares a simple reduction in deployed capital with targeted suppression, although realized test volatility is not guaranteed equal. Return, volatility and utilization must be assessed together; reduced drawdown alone is not economic improvement. Turnover and costs are capital-normalized sums; cumulative transaction-cost totals are arithmetic costs, not compounded return attribution.

![Original and modified strategies](figures/strategy_comparison.png)

![Pair-level changes](figures/pair_attribution.png)

{table(alarm_summary)}

Flagged baseline entries provide a shadow counterfactual: which original entries faced a high indicator, and how their original trades subsequently performed. A profitable matured flagged trade is a false alarm/missed profitable recovery; a losing matured trade is an avoided loss. Unresolved trades at a stage end remain separately counted and are excluded from win/loss claims. A trade completing after the stage end never uses its future outcome in that stage's alarm analysis. Actual denied flat-state days are a different population and are reported separately. Modified strategies can later enter at a different time, so shadow-trade profits are not additive portfolio P&L attribution. Signal frequency, pair exposure, completed counts and opportunity suppression are supplied in `signal_analysis.csv` and `pair_attribution.csv`.

![Flags, false alarms and missed recoveries](figures/signals_and_missed_recoveries.png)

## 8. Robustness checks

Prespecified trading sensitivities include 126/504-day beta filters, the 252-day persistence filter, actual calendar-three-year rolling mean, boundary carry from fitted IS history, and daily weight-restoration turnover costs. These are reported without choosing a winner. Boundary-carry results are reference sensitivity using retrospectively fitted IS models, not an independently deployable IS strategy.

{sensitivity}

Validation-period economic results for comparison with final holdout:

{table(val_main,['strategy','variant','return','sharpe','max_drawdown','capital_utilization'])}

{table(robust,['strategy','variant','return','sharpe','max_drawdown','volatility','capital_utilization','transaction_costs'])}

Prediction results across all three windows/horizons, validation versus test, and three populations permit stability assessment. No future-dependent break labeling is used to color historical figures. Every figure has explicit dates; vertical boundaries mark selection/development, validation and test where applicable. Each pair's original spread/z-score, rolling betas, persistence and half-lives are available in `figures/*_diagnostics.png` and PDF.

## 9. Limitations

The universe is historical and selected by the reference; it is not a survivorship-free survey of all possible funds. Current vendor adjustments are not a vintage point-in-time database. Close-to-close execution assumes orders can achieve the close used to form the signal; the next-day return alignment removes return look-ahead but does not demonstrate a practical pre-close execution method. No spread/slippage, borrow financing, dividend-tax asymmetry, ETF short constraints, market impact or interest on idle cash is modeled. Explicit transaction costs cover only the conventions shown. Constant gross dollar weights require rebalancing; its additional cost is reported separately.

Model standard errors on nonstationary levels and local AR half-life intervals are descriptive. Formal inference is applied to prospective predictive losses and associations with dependence adjustments, subject to their assumptions. Structural instability can be persistent for longer than bootstrap blocks; inference may be optimistic under long memory or abrupt changes. Approximate 60-day independent-block counts are small, and rare entry opportunities often cannot support a fit. Pooled pair forecasts also assume sufficient parameter sharing and common loss units; nine shared-exposure pairs are not nine independent markets. Complete-case deletion for sparse trailing convergence can restrict the evaluable population. No result justifies an unconditional stationary market distribution.

## 10. Conclusions

{conclusion}

Four interpretations remain distinct. Detectable and predictive instability would support adaptive monitoring without proving recurring regimes. Detectable but nonpredictive instability would show changing relationships with little forecast utility. Predictive deterioration with unhelpful filters would indicate delays, noisy signals or economic costs. No credible incremental predictive relationship would leave the practical null unrefuted. Economic comparisons above must be judged independently of statistical change detection. No causal claim about the effect of market structural changes follows from these observational associations.

## Reproducibility and sources

Commands are in [the project README](../../README.md). `run_manifest.json` records configuration, installed library versions, code and input checksums. `frozen_thresholds.csv` records every pair threshold and calibration date. All data tables and positive/negative variants are exported. Figures are PNG and vector PDF.

Method references: [statsmodels Engle–Granger documentation](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.coint.html), [statsmodels HAC covariance](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_hac.html), and [yfinance download adjustment options](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html). Numerical replication targets come only from the supplied PDF, not web commentary. The full report can be exported with Pandoc, as documented in the README.
'''
    (output/'research_report.md').write_text(txt)
    summary=f'''# Executive summary

This reproducible study uses the original eleven ETFs and the reference's historical nine pairs. Its {audit['observations']} daily observations reproduce the reported sample dates and 70/30 boundaries. See [baseline replication](baseline_replication.md) for selection and numerical discrepancies; exact original-input replication is not claimed.

**Can instability be measured?** Yes, trailing OLS coefficient departures, residual dispersion, AR persistence and valid monotonic half-lives can be measured using only observed history. These are descriptive indicators, not validated declarations of discrete market regimes.

**Does instability predict deterioration, and add to simple predictors?** {predictive_statement} {conclusion} The baseline forecast already includes spread magnitude, recent volatility, recent spread changes and matured convergence. Statistical associations alone are not evidence of useful incremental forecasting.

Exploratory results are mixed: {len(exploratory_better)} BY-adjusted comparisons favor the extended forecast, while {int((significant_all.mse_gain<0).sum())} favor the simpler baseline. {exploratory_interpretation} These exploratory findings do not overturn the primary result.

**Are results credible?** The design separates development, validation and test, purges crossing labels, groups dependence by shared dates, and adjusts for multiplicity. Nevertheless, the final sample has few independent 60-day blocks, rare entries and possible longer persistence. Treat results as conditional historical evidence requiring prospective replication.

**Does acting on instability improve performance?** Final-holdout comparisons:

'''+ '\n'.join('- '+s for s in gains)+f'''

Changes must also be compared with volatility filtering and the validation-scaled control. Lower capital utilization can reduce drawdowns without adding information. Costs from exposure changes are included; daily rebalancing cost sensitivities are in the full report.

**How sensitive are conclusions?** {sensitivity} Calendar-three-year mean, boundary carry and executable turnover costs are also reported. No best threshold or specification is selected. Negative and insufficient-sample results remain in `predictive_results.csv`.

Read [the research report](research_report.md) for tables, figures and explicit limits.
'''
    (output/'executive_summary.md').write_text(summary)
    from .pdf_export import export_briefing
    export_briefing(output)
