import streamlit as st
import requests
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator

st.set_page_config(page_title="ETH Signal Bot", layout="centered")
st.title("Ethereum Signal Bot (ETH/USD, CoinGecko)")

def fetch_ohlcv():
    url = "https://api.coingecko.com/api/v3/coins/ethereum/market_chart"
    params = {"vs_currency": "usd", "days": "7", "interval": "hourly"}
    data = requests.get(url, params=params).json()
    prices = data["prices"]
    df = pd.DataFrame(prices, columns=["timestamp", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["close"] = df["close"].astype(float)
    return df

def get_signal(df):
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
