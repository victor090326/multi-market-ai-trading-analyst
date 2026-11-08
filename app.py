import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Multi-Market AI Trading Analyst", page_icon="📊", layout="wide")

st.title("📊 Multi-Market AI Trading Analyst")
st.caption("M2 candle analysis • 30-candle window • 8–12 minute forecast horizon")

with st.sidebar:
    st.header("Market settings")
    market_mode = st.selectbox("Market environment", ["Real Forex", "Quotex OTC"])
    common_pairs = ["EUR/USD", "GBP/USD", "USD/JPY", "GBP/JPY", "AUD/USD", "USD/CAD", "XAU/USD"]
    otc_pairs = ["EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC", "AUD/USD OTC", "Other OTC pair"]
    pair = st.selectbox("Trading pair", otc_pairs if market_mode == "Quotex OTC" else common_pairs)
    timeframe = st.selectbox("Analysis timeframe", ["M2"], index=0)
    max_candles = st.selectbox("Maximum candles to analyse", [30], index=0)
    st.info("This starter version analyses candle data you upload. It does not connect to Quotex or a broker automatically.")

st.subheader("1. Upload candle data")
st.write("Upload a CSV containing at least these columns: **Open, High, Low, Close**. An optional Timestamp column is supported.")
uploaded = st.file_uploader("Choose OHLC CSV file", type=["csv"])

def normalize_columns(frame):
    frame = frame.copy()
    frame.columns = [str(c).strip().lower() for c in frame.columns]
    aliases = {
        "o": "open", "h": "high", "l": "low", "c": "close",
        "timestamp": "timestamp", "time": "timestamp", "date": "timestamp",
        "datetime": "timestamp"
    }
    frame = frame.rename(columns={c: aliases.get(c, c) for c in frame.columns})
    required = ["open", "high", "low", "close"]
    missing = [c for c in required if c not in frame.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))
    for c in required:
        frame[c] = pd.to_numeric(frame[c], errors="coerce")
    frame = frame.dropna(subset=required).reset_index(drop=True)
    if "timestamp" in frame.columns:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    return frame

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def analyse(frame):
    data = frame.tail(30).copy()
    close = data["close"]
    data["ema20"] = close.ewm(span=20, adjust=False).mean()
    data["ema50"] = close.ewm(span=50, adjust=False).mean()
    data["rsi14"] = rsi(close, 14)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    data["macd"] = ema12 - ema26
    data["macd_signal"] = data["macd"].ewm(span=9, adjust=False).mean()

    last = data.iloc[-1]
    points = 0
    reasons = []

    if last["close"] > last["ema20"] and last["ema20"] > last["ema50"]:
        points += 1
        reasons.append("Price is above EMA20 and EMA20 is above EMA50 (bullish trend alignment).")
    elif last["close"] < last["ema20"] and last["ema20"] < last["ema50"]:
        points -= 1
        reasons.append("Price is below EMA20 and EMA20 is below EMA50 (bearish trend alignment).")
    else:
        reasons.append("EMA structure is mixed; trend confirmation is weak.")

    if pd.notna(last["rsi14"]):
        if 50 < last["rsi14"] < 70:
            points += 1
            reasons.append("RSI supports bullish momentum without being overbought.")
        elif 30 < last["rsi14"] < 50:
            points -= 1
            reasons.append("RSI supports bearish momentum without being oversold.")
        elif last["rsi14"] >= 70:
            reasons.append("RSI is overbought; avoid treating this alone as a sell signal.")
        elif last["rsi14"] <= 30:
            reasons.append("RSI is oversold; avoid treating this alone as a buy signal.")
        else:
            reasons.append("RSI is near the midpoint and gives limited directional evidence.")

    if pd.notna(last["macd"]) and pd.notna(last["macd_signal"]):
        if last["macd"] > last["macd_signal"]:
            points += 1
            reasons.append("MACD is above its signal line.")
        elif last["macd"] < last["macd_signal"]:
            points -= 1
            reasons.append("MACD is below its signal line.")

    # Conservative starter rule: require agreement from at least two components.
    if points >= 2:
        decision = "BUY"
        bias = "BULLISH"
    elif points <= -2:
        decision = "SELL"
        bias = "BEARISH"
    else:
        decision = "WAIT"
        bias = "MIXED / UNCLEAR"

    recent_high = data["high"].tail(20).max()
    recent_low = data["low"].tail(20).min()
    return data, last, decision, bias, points, reasons, recent_high, recent_low

if uploaded:
    try:
        raw = pd.read_csv(uploaded)
        candles = normalize_columns(raw)
        if len(candles) < 30:
            st.warning(f"Only {len(candles)} valid candles were found. The target is 30; results may be less reliable.")
        if len(candles) < 20:
            st.error("Please upload at least 20 valid candles for this initial analysis.")
        else:
            data, last, decision, bias, points, reasons, recent_high, recent_low = analyse(candles)
            st.subheader("2. Analysis result")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Market", market_mode)
            c2.metric("Pair", pair)
            c3.metric("Candles analysed", str(len(data)))
            c4.metric("Latest close", f"{last['close']:.5f}")

            st.divider()
            a, b, c = st.columns(3)
            a.metric("Decision", decision)
            b.metric("Trend bias", bias)
            b.metric("Signal score", f"{points:+d} / 3")
            c.metric("Forecast horizon", "8–12 minutes")

            st.subheader("3. Indicator readings")
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("EMA 20", f"{last['ema20']:.5f}")
            d2.metric("EMA 50", f"{last['ema50']:.5f}")
            d3.metric("RSI 14", "N/A" if pd.isna(last["rsi14"]) else f"{last['rsi14']:.2f}")
            d4.metric("MACD", f"{last['macd']:.6f}")

            st.subheader("4. Recent price levels")
            x, y = st.columns(2)
            x.metric("Recent 20-candle high", f"{recent_high:.5f}")
            y.metric("Recent 20-candle low", f"{recent_low:.5f}")

            st.subheader("5. Why the system decided this")
            for reason in reasons:
                st.write("• " + reason)

            st.subheader("6. Latest 30 candles")
            display_cols = [c for c in ["timestamp", "open", "high", "low", "close"] if c in data.columns]
            st.dataframe(data[display_cols].tail(30), use_container_width=True)

            st.warning(
                "Important: this is an initial rule-based research prototype, not a validated predictive model. "
                "The 8–12 minute horizon is a monitoring window, not a guaranteed forecast. "
                "Do not use its output as an instruction to place a live trade. Backtest on separate, time-ordered data first."
            )
    except Exception as exc:
        st.error(f"Could not read/analyse this CSV: {exc}")
else:
    st.info("Upload an OHLC CSV to begin. The app is ready for candle-data testing.")
    st.code("Open,High,Low,Close\n1.1000,1.1010,1.0995,1.1005\n1.1005,1.1015,1.1000,1.1012", language="text")

st.caption("Version 0.1 • CSV-based prototype • Live market connections and OTC-specific data validation are not yet implemented.")
