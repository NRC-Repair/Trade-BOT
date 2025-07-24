import streamlit as st
import requests
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator

st.set_page_config(page_title="ETH Signal Bot", layout="centered")
st.title("Ethereum Signal Bot (ETH/USD, CryptoCompare)")
st.caption("Keine Finanzberatung. Das Signal beruht auf SMA und RSI.")

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

def get_signal_and_probability(df):
    if len(df) < 21:
        return "Zu wenig Daten!", 0
    sma = SMAIndicator(df['close'], window=20).sma_indicator()
    rsi = RSIIndicator(df['close'], window=14).rsi()
    last_close = df['close'].iloc[-1]
    last_sma = sma.iloc[-1]
    last_rsi = rsi.iloc[-1]
    # Wahrscheinlichkeit: Je niedriger der RSI und je weiter der Kurs über dem SMA, desto höher das Kaufsignal
    if last_close > last_sma and last_rsi < 70:
        prob = max(0, min(100, round((70 - last_rsi) * 1.4)))  # z.B. RSI 30 → 56%
        return 'KAUFEN 🚀', prob
    elif last_close < last_sma and last_rsi > 30:
        prob = max(0, min(100, round((last_rsi - 30) * 1.4)))
        return 'VERKAUFEN ⚠️', prob
    else:
        return 'ABWARTEN ⏳', 0

if st.button("Signal abfragen"):
    df = fetch_ohlcv()
    signal, prob = get_signal_and_probability(df)
    st.subheader(f"Aktuelles Signal: {signal}")
    if signal == "KAUFEN 🚀":
        st.metric("Kaufen-Wahrscheinlichkeit", f"{prob} %")
    elif signal == "VERKAUFEN ⚠️":
        st.metric("Verkaufen-Wahrscheinlichkeit", f"{prob} %")
    st.line_chart(df.set_index('timestamp')['close'])
    st.write("Letzte Aktualisierung:", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))
else:
    st.info("Klicke auf den Button, um das aktuelle Signal zu holen.")

st.caption("Dieses Tool ist rein informativ und trifft keine Anlageentscheidung.")
