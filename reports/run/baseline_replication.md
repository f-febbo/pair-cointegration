# Baseline replication assessment

Primary reference: *Pairs Trading on Sector ETFs: Method and Backtest Results*, supplied four-page PDF. Entire document read before implementation; text extraction is preserved in `docs/reference_extracted.txt`. Figures are descriptive context; Tables 1–3 supply numerical targets. No SPY overlay is implemented.

## Data and split

Source: Yahoo Finance via yfinance; Adj Close, auto_adjust=False, repair=False. Retrieval: 2026-10-16T17:06:51.531703+00:00. SHA256: `c0b320f2379a78a89e1efbce02cbd19fd1ee9cae2a84a10bf09844bd9f2c4f6c`.

Sample: 2004-09-29 through 2026-10-08; 5542 common daily observations. In-sample: 3879 observations ending 2020-02-26. Out-of-sample: 1663 observations starting 2020-02-27. Reference boundary match: **True**. Removed incomplete dates: 0. Prices are explicitly vendor adjusted closes; no interpolation or forward filling. The calendar is the intersection of observed sessions, not an independently certified exchange calendar.

## Pair selection

Both Engle–Granger orientations are retained in `all_55_pairs.csv`, with a constant, AIC lag selection, and statsmodels default maximum lag. Original selection retains the lower p-value and uses p < 0.10. Reproduced selection: **9 pairs**; unordered pair-set match: **True**. Reference-only pairs: []; reproduced-only pairs: [].

| pair    |   eg_stat |   p_min |   alpha |   beta |   sigma |   q_bh_naive_min |   q_bh_orientation_corrected |   q_by_orientation_corrected |
|:--------|----------:|--------:|--------:|-------:|--------:|-----------------:|-----------------------------:|-----------------------------:|
| XLU/XLK |   -4.1870 |  0.0038 |  0.6438 | 0.7081 |  0.0807 |           0.2022 |                       0.4044 |                       1.0000 |
| XLU/XLI |   -3.9480 |  0.0085 | -0.4154 | 0.8326 |  0.0856 |           0.2022 |                       0.4044 |                       1.0000 |
| XLB/XLU |   -3.8664 |  0.0110 |  0.5346 | 0.8663 |  0.0926 |           0.2022 |                       0.4044 |                       1.0000 |
| XLV/XLY |   -3.5764 |  0.0262 |  0.8602 | 0.8906 |  0.0797 |           0.3237 |                       0.6474 |                       1.0000 |
| XLB/XLP |   -3.5046 |  0.0320 |  0.3783 | 0.7253 |  0.1053 |           0.3237 |                       0.6474 |                       1.0000 |
| XLI/XLV |   -3.4683 |  0.0353 |  0.3858 | 0.8653 |  0.0872 |           0.3237 |                       0.6474 |                       1.0000 |
| XLU/XLY |   -3.3526 |  0.0479 |  0.4881 | 0.6539 |  0.1040 |           0.3763 |                       0.7526 |                       1.0000 |
| XLB/XLI |   -3.2175 |  0.0671 |  0.0642 | 0.7530 |  0.0680 |           0.4434 |                       0.8868 |                       1.0000 |
| XLB/XLV |   -3.1845 |  0.0726 |  0.3826 | 0.6438 |  0.1075 |           0.4434 |                       0.8868 |                       1.0000 |

Taking the smaller of two p-values is a selection step. Naive BH on the 55 minima is only an illustration; orientation-Bonferroni p=min(1,2p_min), followed by BH and dependence-conservative BY, are separate diagnostics. These do not change the baseline selection. Shared ETFs induce cross-pair dependence. A residual unit-root rejection does not guarantee a stable relationship or profitable trades.

At the reference 10% level, orientation-corrected BH retains 0 pairs and orientation-corrected BY retains 0 pairs, versus the original nine unadjusted selections.

## Historical nine-pair results

The report's nine named pairs are fitted in its reported orientations for direct numerical comparison, even if the winning orientation or selection differs. Portfolios using reproduced selection are saved separately. Extensions refer to the historical nine, not a silently substituted universe.

| pair    |   beta |   sigma |   oos_adf_stat |   oos_adf_p |   static_entries |   static_completed_trades |   static_open_trades |   static_return |   static_sharpe |   rolling_completed_trades |   rolling_return |   rolling_sharpe |
|:--------|-------:|--------:|---------------:|------------:|-----------------:|--------------------------:|---------------------:|----------------:|----------------:|---------------------------:|-----------------:|-----------------:|
| XLU/XLK | 0.7081 |  0.0807 |        -2.0188 |      0.2784 |                1 |                         0 |                    1 |         -0.2933 |         -0.3529 |                          6 |           0.1789 |           0.3036 |
| XLU/XLI | 0.8326 |  0.0856 |        -2.5257 |      0.1093 |                4 |                         3 |                    1 |          0.2423 |          0.5356 |                          4 |           0.2595 |           0.5793 |
| XLB/XLU | 0.8663 |  0.0926 |        -3.3250 |      0.0138 |                5 |                         4 |                    1 |          0.3243 |          0.5414 |                          4 |           0.2496 |           0.5169 |
| XLV/XLY | 0.8906 |  0.0797 |        -2.2035 |      0.2050 |                7 |                         7 |                    0 |          0.5085 |          0.8564 |                          4 |           0.1812 |           0.3766 |
| XLB/XLP | 0.7253 |  0.1053 |        -3.9225 |      0.0019 |                2 |                         1 |                    1 |         -0.0227 |          0.0120 |                          2 |           0.1427 |           0.3593 |
| XLI/XLV | 0.8653 |  0.0872 |        -1.0140 |      0.7481 |                3 |                         2 |                    1 |          0.0303 |          0.0993 |                          1 |          -0.0468 |          -0.0678 |
| XLU/XLY | 0.6539 |  0.1040 |        -2.6128 |      0.0904 |                5 |                         4 |                    1 |          0.4243 |          0.6505 |                          4 |           0.3422 |           0.6405 |
| XLB/XLI | 0.7530 |  0.0680 |        -2.2226 |      0.1981 |                3 |                         3 |                    0 |          0.1689 |          0.5024 |                          2 |          -0.0253 |          -0.0528 |
| XLB/XLV | 0.6438 |  0.1075 |        -2.7712 |      0.0625 |                3 |                         2 |                    1 |          0.1193 |          0.2291 |                          3 |           0.2020 |           0.4375 |

| strategy   | stage     | universe             |   return |   max_drawdown |   sharpe |   delta_return |   delta_max_drawdown |   delta_sharpe |
|:-----------|:----------|:---------------------|---------:|---------------:|---------:|---------------:|---------------------:|---------------:|
| static     | selection | historical_nine      |   0.6623 |        -0.0830 |   0.8957 |         0.0003 |              -0.0000 |        -0.0043 |
| static     | oos       | historical_nine      |   0.1627 |        -0.0622 |   0.5549 |        -0.0003 |              -0.0002 |         0.0049 |
| static     | oos       | reproduced_selection |   0.1627 |        -0.0622 |   0.5549 |       nan      |             nan      |       nan      |
| rolling    | selection | historical_nine      |   0.3386 |        -0.0798 |   0.5339 |        -0.0004 |               0.0002 |         0.0039 |
| rolling    | oos       | historical_nine      |   0.1726 |        -0.0390 |   0.6782 |        -0.0004 |               0.0000 |        -0.0018 |
| rolling    | oos       | reproduced_selection |   0.1726 |        -0.0390 |   0.6782 |       nan      |             nan      |       nan      |

Every pair target has signed, absolute, and relative differences in `baseline_replication_differences.csv`. Portfolio absolute and relative differences are in `baseline_portfolio_metrics.csv`. Maximum absolute beta difference: 0.000382; maximum absolute pair-return difference: 0.000491. Reference inputs are rounded, so small discrepancies are unavoidable. Exact replication is **not certified**: the original raw snapshot and source code were not supplied.

## Explicit implementation choices and discrepancies

The frozen residual is log(Y)−alpha−beta log(X). Spread sigma uses sample ddof=1. Static mean and sigma stay fixed. The primary rolling mean uses 756 observations ending at today's close, including pre-OOS history. The PDF says three years but does not specify calendar years versus trading days. An exact calendar-three-year variant is reported as sensitivity, not selected after observing performance.

The close-t position earns the t→t+1 return. The PDF leaves the precise daily return formula implicit. Numerical reconciliation identifies its convention as q_previous×(s_t−s_(t−1))/(1+|beta|), less 0.0005×|change in scalar spread position|, then compounded as if these log-spread increments were daily simple returns. This matches every reported pair return and both OOS portfolio returns to their rounding. It is a replication approximation, not an exact investable P&L.

In the extensions, a spread direction q maps to daily dollar weights q/(1+|beta|) in Y and −q beta/(1+|beta|) in X. The implementable gross return is q_previous(rY−beta rX)/(1+|beta|), using simple dividend-adjusted leg returns. Negative betas, if present, are normalized using absolute gross exposure. The extensions retain reference scalar-position costs for direct comparison and separately charge turnover needed to restore daily dollar weights as prices drift. Costs from half-exposure changes are included. The reference-log control remains visible as sensitivity; all main filter/control comparisons use the same simple-return convention.

Positions start flat at the OOS boundary, remain in their original direction until |z|≤0.25, and cannot open on the last observed date. No forced end-of-sample liquidation is imposed; open trades are separately counted and marked to market. No immediate reversal or reopening occurs on an exit close. The PDF's single Table 2 trade-count column matches static entries, including still-open trades; treating these as completed trades would misstate the reference. Both entries and genuinely completed trades are reported, with rolling counts newly supplied. Boundary carry and calendar-window variants expose unresolved reference details. IS results use models and pairs fitted on the full IS sample and are retrospective fitted context, not causal validation.

All prices are retrospectively adjusted. Adjustment revisions can shift intercepts, and revised historical relative price paths can change residuals and returns. The downloaded snapshot is preserved; the code does not attribute every discrepancy to a particular cause without original inputs. Baseline assessment is written before diagnostics and predictive analysis execute.
