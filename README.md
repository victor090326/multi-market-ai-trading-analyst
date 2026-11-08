# Multi-Market AI Trading Analyst

A starter Streamlit project for analysing uploaded OHLC candle data.

## Current prototype
- Separate Real Forex / Quotex OTC selection in the interface.
- M2 analysis setting.
- Analyses at most the latest 30 uploaded candles.
- EMA20, EMA50, RSI14 and MACD calculations.
- Conservative BUY / SELL / WAIT rule-based classification.
- Recent 20-candle high and low.
- CSV upload; optional Timestamp column.

## CSV format
Required columns: `Open, High, Low, Close`
Optional: `Timestamp`

The app accepts common short headers such as O, H, L, C as well.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Important limitations
This is a research prototype. It does not yet connect to a broker, retrieve live Forex data, or retrieve Quotex OTC candles. Selecting OTC does not make ordinary Forex data into OTC data. A supported and permitted OTC data source or user-provided OTC candle export is required.

The 8–12 minute horizon is currently displayed as a monitoring horizon, not a validated price forecast. The initial BUY/SELL/WAIT rule is not a guarantee of future movement. Backtest chronologically, include fees/spread and slippage where applicable, and use paper testing before considering any live use.
