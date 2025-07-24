import streamlit as st
import pandas as pd
import numpy as np
import requests
from ta.trend import SMAIndicator, EMAIndicator, MACD, CCIIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands
from ta.volume import OnBalanceVolumeIndicator
import matplotlib.pyplot as plt

st.set_page_config(page_title="ETH Signal Optimizer", layout="wide")
st.title("ETH/USD: Automatisiertes Kaufsignal aus Backtest-Optimierung")
st.caption("Die besten Schwellen werden automatisch aus der Vergangenheit gesucht. Das JETZT-Signal basiert auf dieser Statistik.")

# --- Ziel-Parameter wählbar
col1, col2 = st.columns(2)
with col1:
    profit_thresh = st.slider("Backtest: Ziel-Gewinn (%)", 1, 30, 5)
with col2:
    holding_days = st.slider("Backtest: Haltedauer (Tage)", 5, 90, 30)

# --- Daten holen
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

# --- Indikatoren
def calc_indicators(df):
    df = df.copy()
    df['sma20'] = SMAIndicator(df['close'], 20).sma_indicator()
    df['ema20'] = EMAIndicator(df['close'], 20).ema_indicator()
    macd = MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['rsi14'] = RSIIndicator(df['close'], 14).rsi()
    stoch = StochasticOscillator(df['close'], df['close'], df['close'])
    df['stoch_k'] = stoch.stoch()
    df['stoch_d'] = stoch.stoch_signal()
    bb = BollingerBands(df['close'])
    df['bb_high'] = bb.bollinger_hband()
    df['bb_low'] = bb.bollinger_lband()
    df['obv'] = OnBalanceVolumeIndicator(df['close'], volume=np.ones(len(df))).on_balance_volume()
    df['cci'] = CCIIndicator(df['close'], df['close'], df['close'], 20).cci()
    return df

df = calc_indicators(df)

# --- Optimierung: Grid Search für beste Parameter
def get_signals(df, min_votes, rsi_buy, cci_buy):
    signals = []
    for idx, row in df.iterrows():
        votes = 0
        if row['close'] > row['sma20']: votes += 1
        if row['close'] > row['ema20']: votes += 1
        if row['macd'] > row['macd_signal']: votes += 1
        if row['rsi14'] < rsi_buy: votes += 1
        if row['stoch_k'] < 20 and row['stoch_k'] > row['stoch_d']: votes += 1
        if row['close'] < row['bb_low']: votes += 1
        if row['cci'] < cci_buy: votes += 1
        signals.append(1 if votes >= min_votes else 0)
    return np.array(signals)

def backtest(df, signals, profit_threshold, holding_days):
    buy_rows = df[signals == 1]
    results = []
    for dt in buy_rows.index:
        idx = df.index.get_loc(dt)
        future_idx = min(idx + holding_days, len(df) - 1)
        buy_price = df.loc[dt]['close']
        sell_max = df.iloc[idx+1:future_idx+1]['close'].max()
        reached = (sell_max >= buy_price * (1 + profit_threshold/100))
        results.append(reached)
    if len(results) == 0:
        return 0
    hitrate = 100 * np.sum(results) / len(results)
    return hitrate

st.info("Optimiere: Voting-Schwelle, RSI und CCI… (wird berechnet, kann einige Sekunden dauern)")

best_hitrate = 0
best_params = None

# --- Parameterbereiche fürs Grid Search
for min_votes in range(2, 6):
    for rsi_buy in range(30, 51, 2):
        for cci_buy in range(-150, -49, 10):
            signals = get_signals(df, min_votes, rsi_buy, cci_buy)
            hitrate = backtest(df, signals, profit_thresh, holding_days)
            if hitrate > best_hitrate:
                best_hitrate = hitrate
                best_params = (min_votes, rsi_buy, cci_buy)

min_votes, rsi_buy, cci_buy = best_params
signals = get_signals(df, min_votes, rsi_buy, cci_buy)
df['buy_signal'] = signals

# --- Jetzt-Signal (letzter Tag)
now_signal = int(signals[-1])
now_status = "KAUFEN! 🚀" if now_signal == 1 else "Kein Kaufsignal"

st.success(f"""
**Optimale Parameter aus Backtest:**  
Votes: {min_votes}, RSI < {rsi_buy}, CCI < {cci_buy}  
**Backtest-Trefferquote:** {best_hitrate:.1f} % für +{profit_thresh}% in {holding_days} Tagen
""")

st.subheader(f"**Heutiges Signal:** {now_status}")

st.line_chart(df['close'], use_container_width=True)

# Optional: Signalpunkte plotten
fig, ax = plt.subplots(figsize=(10,4))
ax.plot(df.index, df['close'], label='ETH/USD')
ax.scatter(df[df['buy_signal']==1].index, df[df['buy_signal']==1]['close'], color='lime', marker='o', label='Kaufsignal')
ax.set_title('ETH/USD + Kaufsignale (optimiert)')
ax.legend()
st.pyplot(fig)

st.caption("Das heutige Signal basiert auf den best-getroffenen Schwellen der Vergangenheit (Backtest-Optimierung). Keine Finanzberatung.")
