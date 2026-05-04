#!/usr/bin/env python3
"""Simple Alpaca paper-trading bot using SMA crossover strategy."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class Config:
    api_key: str
    secret_key: str
    base_url: str = "https://paper-api.alpaca.markets/v2"
    data_url: str = "https://data.alpaca.markets/v2"
    symbol: str = "AAPL"
    qty: int = 1
    fast_window: int = 5
    slow_window: int = 20
    poll_interval_sec: int = 60


class AlpacaClient:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "APCA-API-KEY-ID": config.api_key,
                "APCA-API-SECRET-KEY": config.secret_key,
                "accept": "application/json",
            }
        )

    def _get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self.session.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json()

    def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.session.post(url, json=payload, timeout=20)
        response.raise_for_status()
        return response.json()

    def get_latest_bars(self, symbol: str, limit: int) -> list[dict[str, Any]]:
        payload = self._get(
            f"{self.config.data_url}/stocks/{symbol}/bars",
            params={"timeframe": "1Min", "limit": limit},
        )
        return payload.get("bars", [])

    def get_position_qty(self, symbol: str) -> int:
        try:
            payload = self._get(f"{self.config.base_url}/positions/{symbol}")
            return int(float(payload.get("qty", 0)))
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                return 0
            raise

    def submit_market_order(self, symbol: str, qty: int, side: str) -> dict[str, Any]:
        return self._post(
            f"{self.config.base_url}/orders",
            {
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "type": "market",
                "time_in_force": "gtc",
            },
        )


def simple_moving_average(values: list[float]) -> float:
    return sum(values) / len(values)


def run_bot(config: Config) -> None:
    client = AlpacaClient(config)
    print(f"Starting bot for {config.symbol} on {config.base_url}")

    while True:
        try:
            bars = client.get_latest_bars(config.symbol, config.slow_window)
            if len(bars) < config.slow_window:
                print("Waiting for enough bars...")
                time.sleep(config.poll_interval_sec)
                continue

            closes = [float(bar["c"]) for bar in bars]
            fast_sma = simple_moving_average(closes[-config.fast_window :])
            slow_sma = simple_moving_average(closes[-config.slow_window :])
            position_qty = client.get_position_qty(config.symbol)

            print(
                f"fast_sma={fast_sma:.2f}, slow_sma={slow_sma:.2f}, "
                f"position_qty={position_qty}"
            )

            if fast_sma > slow_sma and position_qty <= 0:
                order = client.submit_market_order(config.symbol, config.qty, "buy")
                print(f"BUY order submitted: {order.get('id')}")
            elif fast_sma < slow_sma and position_qty > 0:
                order = client.submit_market_order(config.symbol, position_qty, "sell")
                print(f"SELL order submitted: {order.get('id')}")

        except requests.HTTPError as exc:
            message = exc.response.text if exc.response is not None else str(exc)
            print(f"HTTP error: {message}")
        except Exception as exc:  # keep bot running
            print(f"Unexpected error: {exc}")

        time.sleep(config.poll_interval_sec)


def load_config() -> Config:
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")

    if not api_key or not secret_key:
        raise ValueError(
            "Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables before running."
        )

    return Config(
        api_key=api_key,
        secret_key=secret_key,
        symbol=os.getenv("BOT_SYMBOL", "AAPL"),
        qty=int(os.getenv("BOT_QTY", "1")),
        fast_window=int(os.getenv("BOT_FAST_WINDOW", "5")),
        slow_window=int(os.getenv("BOT_SLOW_WINDOW", "20")),
        poll_interval_sec=int(os.getenv("BOT_POLL_INTERVAL_SEC", "60")),
    )


if __name__ == "__main__":
    run_bot(load_config())
