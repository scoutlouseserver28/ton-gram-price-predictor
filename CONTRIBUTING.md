# Contributing to ton-gram-price-predictor

Thanks for wanting to push the TON (GRAM) price predictor forward. This repo
is maintained by a small group of quant hobbyists and TON ecosystem
tinkerers. Contributions of features, model ideas, data adapters, and
backtesting improvements are all welcome.

## Development setup

```bash
git clone https://github.com/ton-gram-labs/ton-gram-price-predictor
cd ton-gram-price-predictor
python -m venv .venv
. .venv/Scripts/activate   # PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Branching

- `main` — stable, tagged releases only.
- `dev` — integration branch, all PRs target here first.
- `feat/<scope>`, `fix/<scope>`, `model/<experiment-name>` — working branches.

## Running the test suite

```bash
pytest
ruff check src tests
mypy src
```

CI runs all three on every PR. A red `mypy` block will not be merged.

## Adding a data source

1. Drop a new adapter under `src/ton_price_predictor/services/`.
2. Subclass `MarketDataAdapter` from `services/base.py`.
3. Register it in `config/sources.yaml`.
4. Add a fixture under `tests/fixtures/` and a test in `tests/`.

## Adding a model

Models live under `src/ton_price_predictor/models/`. Every model must
implement `BaseForecaster` with `fit`, `predict`, and `feature_names`.
Keep them deterministic under a fixed seed — backtest reproducibility is
non-negotiable.

## Commit style

Conventional Commits. Example:

```
feat(models): add quantile LightGBM forecaster for 24h TON/USDT horizon
fix(services): handle 429 backoff on tonapi.io historical endpoint
```

## Reporting issues

Include: Python version, OS, the exact command you ran, the full traceback,
and the contents of `config/settings.yaml` with secrets redacted.