import streamlit as st
import pandas as pd
import numpy as np
import requests
from ta.trend import SMAIndicator, EMAIndicator, MACD, CCIIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands
from ta.volume import OnBalanceVolumeIndicator
import matplotlib.pyplot as plt

st.set_page_config(page_title="ETH Backtest Multi-Indikator", layout="wide")
st.title("ETH/USD Backtest: Kombinierte Kaufsignale aus mehreren Indikatoren (letzte 5 Jahre)")
st.caption("Alle Indikatoren liefern ein Teilsignal. Das endgültige Signal ist das Mehrheitsvotum aller. Es wird getestet, wie viele Kaufsignale nachträglich richtig waren.")

# 1. Hole historische ETH/USD-Daten (CryptoCompare API, Tagesdaten, 5 Jahre)
@st.cache_data(show_spinner=True)
def fetch_data():
    url = "https://min-api.cryptocompare.com/data/v2/histoday"
    params = {"fsym": "ETH", "tsym": "USD", "limit": 1825}
    r = requests.get(url, params=params)
    data = r.json()
    if 'Data' not in data or 'Data' not in data['Data']:
        st.error(f"Fehler: {data}")
        st.stop()
    raw = data['Data']['Data']
    df = pd.DataFrame(raw)
    df['date'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('date', inplace=True)
    df['close'] = df['close'].astype(float)
    return df

df = fetch_data()

# 2. Berechne Indikatoren
def calc_indicators(df):
    df = df.copy()
    # SMA/EMA
    df['sma20'] = SMAIndicator(df['close'], 20).sma_indicator()
    df['ema20'] = EMAIndicator(df['close'], 20).ema_indicator()
    # MACD
    macd = MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    # RSI
    df['rsi14'] = RSIIndicator(df['close'], 14).rsi()
    # Stochastic
    stoch = StochasticOscillator(df['close'], df['close'], df['close'])
    df['stoch_k'] = stoch.stoch()
    df['stoch_d'] = stoch.stoch_signal()
    # Bollinger Bands
    bb = BollingerBands(df['close'])
    df['bb_high'] = bb.bollinger_hband()
    df['bb_low'] = bb.bollinger_lband()
    # OBV (mit Dummy-Volumen, da CryptoCompare kein Volumen liefert)
    df['obv'] = OnBalanceVolumeIndicator(df['close'], volume=np.ones(len(df))).on_balance_volume()
    # CCI
    df['cci'] = CCIIndicator(df['close'], df['close'], df['close'], 20).cci()
    return df

df = calc_indicators(df)

# 3. Signalregeln pro Indikator (7 Indikatoren)
def get_signals(df):
    signals = []
    for idx, row in df.iterrows():
        votes = 0
        # SMA/EMA
        if row['close'] > row['sma20']: votes += 1
        if row['close'] > row['ema20']: votes += 1
        # MACD
        if row['macd'] > row['macd_signal']: votes += 1
        # RSI
        if row['rsi14'] < 35: votes += 1
        # Stochastic
        if row['stoch_k'] < 20 and row['stoch_k'] > row['stoch_d']: votes += 1
        # Bollinger: Preis unter Band = Kaufzone
        if row['close'] < row['bb_low']: votes += 1
        # CCI
        if row['cci'] < -100: votes += 1
        # Wenn mindestens 4 von 7 Kriterien erfüllt: Kaufsignal
        signals.append(1 if votes >= 4 else 0)
    df['buy_signal'] = signals
    return df

df = get_signals(df)

# 4. Backtest-Logik: Kaufsignal → Check ob +5% in den nächsten 30 Tagen
def backtest(df, profit_threshold=0.05, holding_days=30):
    buy_dates = df[df['buy_signal'] == 1].index
    results = []
    for dt in buy_dates:
        idx = df.index.get_loc(dt)
        future_idx = min(idx + holding_days, len(df) - 1)
        buy_price = df.iloc[idx]['close']
        max_future = df.iloc[idx+1:future_idx+1]['close'].max()
        if max_future >= buy_price * (1 + profit_threshold):
            results.append(True)
        else:
            results.append(False)
    if len(results) == 0:
        return 0, 0, []
    hitrate = 100 * np.sum(results) / len(results)
    return len(results), round(hitrate,1), buy_dates[results]

num_signals, hitrate, hit_dates = backtest(df)

# 5. Plotten
st.line_chart(df['close'], use_container_width=True)
st.markdown(f"**Gefundene Kaufsignale (letzte 5 Jahre):** {num_signals}")
st.markdown(f"**Davon richtig (max +5% in 30 Tagen):** {hitrate} %")
st.write("Grüne Punkte = Kaufsignal")

# Signalpunkte im Chart markieren
fig, ax = plt.subplots(figsize=(10,4))
ax.plot(df.index, df['close'], label='ETH/USD')
ax.scatter(df[df['buy_signal']==1].index, df[df['buy_signal']==1]['close'], color='lime', marker='o', label='Kaufsignal')
ax.set_title('ETH/USD + Kaufsignale')
ax.legend()
st.pyplot(fig)

st.caption("Backtest: Ein Kaufsignal zählt als Treffer, wenn der Kurs danach innerhalb von 30 Tagen mindestens 5% steigt. Die Logik und Indikatoren sind ein einfaches Beispiel und keine Anlageberatung.")
