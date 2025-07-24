import streamlit as st
import requests
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator

st.set_page_config(page_title="Top 10 Crypto Signal Bot", layout="wide")
st.title("Top 10 Krypto Signal Bot (CryptoCompare)")
st.caption("Alle Signale & Wahrscheinlichkeiten für die 10 größten Coins auf einen Klick. Keine Finanzberatung!")

TOP10 = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "USDT": "Tether",
    "BNB": "BNB",
    "SOL": "Solana",
    "XRP": "XRP",
    "USDC": "USD Coin",
    "DOGE": "Dogecoin",
    "TON": "Toncoin",
    "ADA": "Cardano"
}

def fetch_ohlcv(symbol="BTC", currency="USD"):
    url = "https://min-api.cryptocompare.com/data/v2/histohour"
    params = {"fsym": symbol, "tsym": currency, "limit": 168}  # 1 Woche, 1-Stunden-Kerzen
    r = requests.get(url, params=params)
    data = r.json()
    if "Data" not in data or "Data" not in data["Data"]:
        return None
    raw = data["Data"]["Data"]
    df = pd.DataFrame(raw)
    df["timestamp"] = pd.to_datetime(df["time"], unit="s")
    df["close"] = df["close"].astype(float)
    return df

def get_signal_and_probability(df):
    if df is None or len(df) < 21:
        return "Keine Daten", 0
    sma = SMAIndicator(df['close'], window=20).sma_indicator()
    rsi = RSIIndicator(df['close'], window=14).rsi()
    last_close = df['close'].iloc[-1]
    last_sma = sma.iloc[-1]
    last_rsi = rsi.iloc[-1]
    if last_close > last_sma and last_rsi < 70:
        prob = max(0, min(100, round((70 - last_rsi) * 1.4)))
        return 'KAUFEN 🚀', prob
    elif last_close < last_sma and last_rsi > 30:
        prob = max(0, min(100, round((last_rsi - 30) * 1.4)))
        return 'VERKAUFEN ⚠️', prob
    else:
        return 'ABWARTEN ⏳', 0

if st.button("Alle Top 10 Krypto-Signale anzeigen"):
    for coin, name in TOP10.items():
        st.markdown(f"### {name} ({coin}/USD)")
        df = fetch_ohlcv(symbol=coin, currency="USD")
        signal, prob = get_signal_and_probability(df)
        st.write(f"**Signal:** {signal}")
        if signal == "KAUFEN 🚀":
            st.metric("Kaufen-Wahrscheinlichkeit", f"{prob} %")
        elif signal == "VERKAUFEN ⚠️":
            st.metric("Verkaufen-Wahrscheinlichkeit", f"{prob} %")
        if df is not None and len(df) > 0:
            st.line_chart(df.set_index('timestamp')['close'])
            st.write("Letzte Aktualisierung:", pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'))
        else:
            st.warning("Keine oder zu wenige Preisdaten vorhanden!")
        st.divider()
else:
    st.info("Klicke auf den Button, um alle aktuellen Top-10-Signale zu erhalten.")

st.caption("Dieses Tool ist rein informativ und trifft keine Anlageentscheidung.")
