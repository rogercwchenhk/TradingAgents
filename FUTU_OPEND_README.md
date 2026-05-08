# TradingAgents with Futu OpenD Integration

Fork of [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) with **Futu OpenD** as an additional data source.

## What is Futu OpenD?

[Futu OpenD](https://openapi.futunn.com/futu-api-doc/opend/opend.html) is a local gateway that provides programmatic access to Futu's market data API. It supports:

- **US and HK stock markets**
- Historical and real-time K-line (OHLCV) data
- Company fundamentals and financial reports
- Market news and capital flow data

## Setup

### 1. Install Futu OpenD

Download and install [Futu OpenD](https://openapi.futunn.com/futu-api-doc/opend/opend.html) on your machine. Start the OpenD gateway before running TradingAgents.

### 2. Install Dependencies

```bash
pip install .
```

The `futu-api` package is included in `pyproject.toml`.

### 3. Configure Futu OpenD

In your TradingAgents config, set the data vendor to `futu_opend`:

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()

# Use Futu OpenD for all data categories
config["data_vendors"] = {
    "core_stock_apis": "futu_opend",
    "technical_indicators": "futu_opend",
    "fundamental_data": "futu_opend",
    "news_data": "futu_opend",
}

# Futu OpenD connection settings
config["futu_opend_host"] = "127.0.0.1"  # Default OpenD host
config["futu_opend_port"] = 11111         # Default OpenD port
config["futu_market"] = "US"              # "US" or "HK"

ta = TradingAgentsGraph(debug=True, config=config)
_, decision = ta.propagate("AAPL", "2026-01-15")
print(decision)
```

### 4. Environment Variables

Alternatively, configure via environment variables:

```bash
export FUTU_OPEND_HOST=127.0.0.1
export FUTU_OPEND_PORT=11111
export FUTU_MARKET=US
```

### 5. Mixed Vendor Configuration

You can mix Futu OpenD with other vendors:

```python
config["data_vendors"] = {
    "core_stock_apis": "futu_opend",       # Futu for OHLCV
    "technical_indicators": "futu_opend",   # Futu for indicators
    "fundamental_data": "yfinance",         # yfinance for fundamentals
    "news_data": "alpha_vantage",           # Alpha Vantage for news
}
```

## Futu OpenD Features

| Feature | Futu OpenD Support |
|---------|-------------------|
| OHLCV Data | ✅ US + HK markets |
| Technical Indicators | ✅ Calculated locally (SMA, EMA, MACD, RSI, Bollinger, ATR, VWMA, MFI) |
| Fundamentals | ✅ Basic info + market snapshot |
| Financial Reports | ✅ Balance sheet, cashflow, income via Futu API |
| News | ✅ Stock-specific + global news |
| Insider Transactions | ⚠️ Capital flow data (proxy for insider transactions) |

## Ticker Format

Futu uses a `MARKET.CODE` format. The integration handles conversion automatically:

- US stocks: `AAPL` → `US.AAPL`
- HK stocks: `00700` → `HK.00700`
- Explicit format: `US.AAPL` or `HK.00700` passed through as-is

Set `futu_market` in config to control the default market.

## Notes

- Futu OpenD must be running locally before starting TradingAgents
- For HK stocks, set `futu_market` to `"HK"` in the config
- Technical indicators are calculated locally from OHLCV data (not from Futu's API)
- Futu OpenD has rate limits; the integration includes fallback to other vendors
