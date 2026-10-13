"""Command-line entrypoint for the TON (GRAM) price predictor."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console

from ton_price_predictor.config.loader import load_settings
from ton_price_predictor.core.pipeline import PredictionPipeline
from ton_price_predictor.services.market_data import MarketDataService

app = typer.Typer(help="TON (GRAM) price predictor CLI", no_args_is_help=True)
console = Console()


@app.command()
def fetch(
    days: int = typer.Option(365, help="History window in days"),
    symbol: str = typer.Option("TONUSDT", help="Spot symbol"),
) -> None:
    """Fetch and cache OHLCV + on-chain history."""
    settings = load_settings()
    svc = MarketDataService(settings)
    rows = asyncio.run(svc.refresh(symbol=symbol, days=days))
    console.print(f"[green]cached {rows} rows for {symbol}[/green]")


@app.command()
def predict(
    horizon: int = typer.Option(24, help="Forecast horizon in hours"),
    symbol: str = typer.Option("TONUSDT", help="Spot symbol"),
) -> None:
    """Run the ensemble forecaster and print a point estimate + band."""
    settings = load_settings()
    pipe = PredictionPipeline(settings)
    result = pipe.predict(symbol=symbol, horizon_hours=horizon)
    console.print(result.as_table())


@app.command()
def backtest(
    config: Path = typer.Option(Path("config/settings.yaml")),
) -> None:
    """Replay the strategy over the configured window."""
    settings = load_settings(config)
    pipe = PredictionPipeline(settings)
    report = pipe.backtest()
    console.print(report.summary())


if __name__ == "__main__":
    app()