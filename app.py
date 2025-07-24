import streamlit as st
import requests
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator

st.set_page_config(page_title="ETH Signal Bot", layout="centered")
st.title("Ethereum Signal Bot (ETH/USD, CryptoCompare)")

def fetch_ohlcv():
    url = "https://min-api.cryptocompare.com/data/v2/histohour"
    params = {"fsym": "ETH", "tsym": "USD", "limit": 168}  # 1 Woche, 1-Stunden-Kerzen
    r = requests.get(url, params=params)
    data = r.json()
    if "Data" not in data or "Data" not in data["Data"]:
        st.error(f"API Fehler: {data}")
        st.stop()
    raw = data["Data"]["Data"]
    df = pd.DataFrame(raw)
    df["timestamp"] = pd.to_datetime(df["time"], unit="s")
    df["close"] = df["close"].astype(float)
    return df

def get_signal(df):
    if len(df) < 21:
        return "Zu wenig Daten!"
    sma = SMAIndicator(df['close'], window=20).sma_indicator()
    rsi = RSIIndicator(df['close'], window=14).rsi()
    last_close = df['close'].iloc[-1]
    last_sma = sma.iloc[-1]
    last_rsi = rsi.iloc[-1]
    if last_close > last_sma and last_rsi < 70:
        return 'KAUFEN 🚀'
    elif last_close < last_sma and last_rsi > 30:
        return 'VERKAUFEN ⚠️'
    else:
        return 'ABWARTEN ⏳'

if st.button("Signal abfragen"):
    df = fetch_ohlcv()
    signal = get_signal(df)
    st.subheader(f"Aktuelles Signal: {signal}")
    st.line_chart(df.set_index('timestamp')['close'])
else:
    st.info("Klicke auf den Button, um das aktuelle Signal zu holen.")

st.caption("Dieses Tool ist rein informativ, keine Finanzberatung.")
