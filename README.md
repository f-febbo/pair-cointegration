# Sector ETF relationship instability research

A reproducible Python study of whether observable changes in historically cointegrated sector ETF relationships predict subsequent convergence and trading deterioration. Read the [research protocol](docs/research_protocol.md) before interpreting results.

## Exploratory strategy iterations

The follow-up study tests ten fixed candidates across local instability calibration, shorter equilibrium memory and time-out/reset strategies. It preserves the original replication and negative primary findings. Some variants improve historical return and Sharpe, but none establishes a stage-family-adjusted paired net-return advantage. The historical test has already been viewed, so every follow-up result is explicitly exploratory.

- [Iteration summary](reports/iterations/summary.md)
- [All strategies, cost stress, statistical checks and walk-forward results](reports/iterations/report.md)
- [Fixed iteration protocol](experiments/protocol.md)
- [Validation-only prospective paper candidate](reports/iterations/prospective_candidate.json)

Run the complete declared batch, retaining every positive and negative variant:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m experiments.run
```

The new rules use simple leg returns and charge actual daily leg turnover. Reports include the same candidates at five and ten basis points. `reports/iterations/daily/` preserves all portfolio series. The future paper start is October 19, 2026; no prospective returns or live trades are claimed.

The supplied four-page reference was read in full. Its [PDF](docs/reference.pdf) and [extracted text](docs/reference_extracted.txt) are preserved. Raw Yahoo downloads, a common-calendar adjusted-close CSV, and SHA256 provenance are included under `data/yahoo_20261016/`. Synthetic data are used only by unit tests. Redundant daily original-study pair files and the large generated outcome panel are excluded from Git and can be rebuilt with the complete pipeline.

## Results

- [Executive summary](reports/run/executive_summary.md)
- [Research report](reports/run/research_report.md)
- [Baseline replication and discrepancies](reports/run/baseline_replication.md)
- [All 55 tests and both orientations](reports/run/all_55_pairs.csv)
- [Predictive results, including negative/insufficient cases](reports/run/predictive_results.csv)
- [Trading comparisons](reports/run/strategy_results.csv)
- [Figures](reports/run/figures/)

The reference's numerical returns correspond to normalized log-spread increments compounded as daily returns. Baseline replication preserves that approximation. Economic extensions use simple dividend-adjusted leg returns, with daily leg-rebalancing costs shown separately. Reported reference trade counts match entries; completed and open trades are distinguished. Full implementation decisions are in the baseline assessment.

## Setup

Python 3.11 or newer (this run uses Python 3.12). A normal setup is:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m pip install --no-deps -e .
```

On Debian/Ubuntu, if `ensurepip` is unavailable, install the matching `python3-venv` system package or use an existing system pip with its `--python` option:

```bash
python3 -m venv --without-pip .venv
pip3 --python .venv install -r requirements-lock.txt
```

Module commands below work directly from the repository without editable installation. `pyproject.toml` declares direct dependencies; `requirements-lock.txt` pins the complete environment used. Network is needed only to install dependencies or acquire a new data snapshot. This environment was bootstrapped using system pip's `--python` option.

## Reproduce from the preserved raw-data snapshot

```bash
.venv/bin/python -m pytest -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m sector_pairs.cli run \
  --data data/yahoo_20261016/adjusted_close.csv --output reports/run
```

`run` validates the input checksum, calendar and split; runs all 55 cointegration tests; writes a baseline assessment before any extension; constructs causal diagnostics/forward labels; evaluates predictions; applies frozen trading filters; and writes tables, PNG/vector-PDF figures, reports and a run manifest. It never changes the dataset. The default bootstrap has 499 replications and a deterministic seed. Runtime depends on BLAS configuration; single-threaded BLAS prevents overhead for these small regressions.

To create an independently timestamped vendor snapshot from raw downloads:

```bash
.venv/bin/python -m sector_pairs.cli download --data data/new_snapshot/adjusted_close.csv
.venv/bin/python -m sector_pairs.cli run --data data/new_snapshot/adjusted_close.csv --output reports/new_snapshot
```

Downloads refuse to overwrite an existing adjusted-close snapshot. Prices use Yahoo `Adj Close`, explicitly `auto_adjust=False`, `repair=False`, and preserve raw Close/Adj Close/actions. Inclusive sample end is converted to the provider's exclusive end. All eleven assets are required. Calendar treatment is an intersection of observed sessions with no interpolation or filling; missing dates are audited. All-asset absent sessions need an independent exchange calendar to detect. Revised downloads may change results; never replace the frozen source silently.

For your own adjusted-price CSV, supply exactly the original eleven columns, a unique increasing Date index, and an adjacent `manifest.json` with nonempty `source`, `adjustment`, and a matching `sha256`. The loader never substitutes raw closes. Manifest declarations require independent source verification for external data; a checksum alone does not establish dividend adjustment.

## Individual stages and experiments

```bash
# Baseline only, including historical-nine and reproduced-selection portfolios
.venv/bin/python -m sector_pairs.cli baseline --output reports/baseline

# Rerun forecasts from the exported panel without acquiring data or trading again
.venv/bin/python -m sector_pairs.cli evaluate --output reports/run

# Rebuild aggregate figures or Markdown reports from exported tables
.venv/bin/python -m sector_pairs.cli figures --output reports/run
.venv/bin/python -m sector_pairs.cli report --output reports/run
```

For individual diagnostic/outcome/trading experiments, use the public Python modules and `dataclasses.replace(Config(), ...)` in a separately named output directory. All three prespecified windows/horizons and every trading sensitivity execute in the standard run. Configuration changes create a new exploratory experiment; do not choose a winner using test results and call that independent evidence. The `run_manifest.json` records exact configuration, package versions, source hashes and input hash. A quick debugging run can reduce `--bootstrap-reps`; use the default 499 for the delivered report.

Report PDF export with an installed Pandoc/TeX distribution:

```bash
cd reports/run
pandoc research_report.md --standalone --pdf-engine=xelatex -o research_report.pdf
```

PNG and vector-PDF versions of every plot are generated without Pandoc. The Markdown is the full authoritative report; the generated `research_briefing.pdf` is a convenient table/figure briefing if present.

## Code organization

| Module | Responsibility |
|---|---|
| `data.py` | Vendor acquisition, source preservation, checksums, shared-calendar validation, chronological stages |
| `cointegration.py` | Both orientations, frozen OLS, original selection, FDR diagnostics, OOS ADF |
| `strategy.py` | Close-signal timing, reference-log/simple-leg P&L, frozen/rolling mean, filters, costs, trade ledgers |
| `diagnostics.py` | Causal rolling alpha/beta, descriptive instability, frozen-spread AR, valid half-lives |
| `outcomes.py` | Strictly future convergence, adverse movement, trade populations, future AR, boundary purge |
| `evaluation.py` | Development fits, baseline/extended predictions, shared-date HAC, bootstrap, multiplicity |
| `performance.py` | Gross-capital metrics, equal allocated portfolios, initial-capital-aware drawdown |
| `reference.py` | Rounded published numerical targets and absolute/relative differences |
| `figures.py`, `reporting.py` | Publication-readable plots, Markdown assessment and conclusions |
| `pipeline.py`, `cli.py` | Ordered stages and reproducible commands |

## Output units and interpretation

Returns, volatility, costs and drawdowns are decimal fractions. Turnover is summed gross exposure traded per dollar allocated; costs are arithmetic capital-normalized totals. Sharpe is annualized with 252 sessions and zero risk-free rate. Equal allocation leaves unused capital in zero-yield cash; shared ETF legs are not netted across pairs. Pair attribution is a difference in compounded pair returns, not an additive attribution of compounded portfolio return.

`*_baseline.csv` uses the reference-log convention. `*_control_portfolio.csv` and modification files in the complete research run use simple leg returns. `*_reference_log_control_portfolio.csv` preserves the approximation for comparison. `predictive_panel.csv.gz` contains both history-only feature columns and explicitly labeled future outcomes; never pass future columns into trading. Feature exports contain prospective dates only. Plots of original fitted IS spreads are hindsight fitted context.

Tests cover next-day return alignment, exit and exposure-change costs, preservation of existing positions under entry filtering, invariance to changed future prices, future-only label support, frozen-t equilibrium, near-zero denominators, invalid half-lives, purge boundaries, initial-capital drawdown, and held-direction continuation after spread sign changes.

No discrete regime labels, hidden Markov models, complex classifiers, threshold optimization, multi-asset baskets or SPY extensions are included. Descriptive local estimates do not validate cointegration or ordinary nonstationary-regression break-test critical values. Chronological validation, dependence adjustment and multiplicity improve credibility but do not remove historical selection, vintage-data limitations, small effective sample size or execution assumptions. Negative results are valid outcomes of this study.
