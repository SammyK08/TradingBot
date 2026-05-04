# TradingBot

A simple Python trading bot for Alpaca's **paper** trading API using `https://paper-api.alpaca.markets/v2`.

## Strategy

The bot uses a 1-minute SMA crossover:

- Compute fast SMA (default 5 bars)
- Compute slow SMA (default 20 bars)
- Buy when fast SMA crosses above slow SMA and no long position exists
- Sell when fast SMA crosses below slow SMA and a long position exists

## Setup

1. Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment variables:

```bash
cp .env.example .env
# edit .env with your Alpaca credentials
```

Or export directly:

```bash
export ALPACA_API_KEY="..."
export ALPACA_SECRET_KEY="..."
```

3. Run the bot:

```bash
python bot.py
```

## Optional config

- `BOT_SYMBOL` (default `AAPL`)
- `BOT_QTY` (default `1`)
- `BOT_FAST_WINDOW` (default `5`)
- `BOT_SLOW_WINDOW` (default `20`)
- `BOT_POLL_INTERVAL_SEC` (default `60`)

## Notes

- This is for educational use and paper trading only.
- Monitor logs and risk before using live endpoints.
