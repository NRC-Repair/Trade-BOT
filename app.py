import streamlit as st
import pandas as pd
import numpy as np
import requests
from ta.trend import SMAIndicator, EMAIndicator, MACD, CCIIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands
from ta.volume import OnBalanceVolumeIndicator
import matplotlib.pyplot as plt

st.set_page_config(page_title="ETH Backtest Feintuning", layout="wide")
st.title("ETH/USD Backtest: Multi-Indikator – Feintuning & Treffer-Statistik")

# --- Parameter-Steuerung
col1, col2, col3 = st.columns(3)
with col1:
    min_votes = st.slider("Minimale Indikator-Votes für Kaufsignal", 2, 7, 3)
with col2:
    rsi_buy = st.slider("RSI-Schwelle (drunter = kaufen)", 20, 50, 40)
    cci_buy = st.slider("CCI-Schwelle (drunter = kaufen)", -200, 0, -80)
with col3:
    profit_thresh = st.slider("Backtest: Ziel-Gewinn (%)", 1, 30, 5)
    holding_days = st.slider("Backtest: Haltedauer (Tage)", 5, 90, 30)

# --- Daten holen (CryptoCompare)
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

# --- Signals/Regeln mit anpassbaren Schwellen
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
    df['buy_signal'] = signals
    return df

df = get_signals(df, min_votes, rsi_buy, cci_buy)

# --- Backtest
def backtest(df, profit_threshold, holding_days):
    buy_rows = df[df['buy_signal'] == 1]
    records = []
    for idx, (dt, row) in enumerate(buy_rows.iterrows()):
        df_idx = df.index.get_loc(dt)
        future_idx = min(df_idx + holding_days, len(df) - 1)
        buy_price = row['close']
        sell_max = df.iloc[df_idx+1:future_idx+1]['close'].max()
        reached = (sell_max >= buy_price * (1 + profit_threshold/100))
        records.append({
            'Kaufdatum': dt,
            'Kurs (Kauf)': round(buy_price,2),
            'Max. Kurs (Haltedauer)': round(sell_max,2),
            'Erreicht?': '✔️' if reached else '❌',
            'Gewinn (%)': round((sell_max/buy_price - 1)*100, 2)
        })
    if not records:
        return pd.DataFrame(), 0
    df_hits = pd.DataFrame(records)
    hitrate = 100 * (df_hits['Erreicht?'] == '✔️').sum() / len(df_hits)
    return df_hits, hitrate

df_hits, hitrate = backtest(df, profit_thresh, holding_days)

# --- Visualisierung
st.line_chart(df['close'], use_container_width=True)
st.markdown(f"**Gefundene Kaufsignale:** {len(df_hits)}")
st.markdown(f"**Trefferquote (+{profit_thresh}% in {holding_days} Tagen):** {hitrate:.1f} %")
st.write("Grüne Punkte = Kaufsignal")

fig, ax = plt.subplots(figsize=(10,4))
ax.plot(df.index, df['close'], label='ETH/USD')
ax.scatter(df[df['buy_signal']==1].index, df[df['buy_signal']==1]['close'], color='lime', marker='o', label='Kaufsignal')
ax.set_title('ETH/USD + Kaufsignale')
ax.legend()
st.pyplot(fig)

if len(df_hits) > 0:
    st.markdown("### Signal- und Backtest-Tabelle")
    st.dataframe(df_hits)
else:
    st.warning("Keine Kaufsignale gefunden – passe die Parameter an.")

st.caption("Experimentiere mit Schwellenwerten, Votes, Gewinnziel & Haltedauer – so findest du bessere Strategien! Keine Finanzberatung.")
