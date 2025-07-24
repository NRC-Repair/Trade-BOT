import streamlit as st
import requests
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
import time

st.set_page_config(page_title="ETH Signal Bot", layout="centered")
st.title("Ethereum Signal Bot (ETH/USD, CryptoCompare)")
st.caption("Automatische Aktualisierung alle 60 Sekunden. Keine Finanzberatung!")

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
    last_close_
