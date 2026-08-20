import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
import os

# --- PAGE SETUP ---
st.set_page_config(page_title="Janta AI Trading House", layout="wide")

# --- THEME ---
st.markdown("""
    <style>
    .main { background-color: #000000; color: #FFD700; }
    .stMetric { background-color: #1a1a1a; border: 2px solid #FFD700; border-radius: 12px; padding: 15px; }
    div[data-testid="stMetricValue"] { color: #FFD700 !important; font-weight: bold; }
    .stButton>button { background-color: #FFD700; color: black; font-weight: 900; border-radius: 8px; width: 100%; height: 50px; font-size: 18px; border: none; }
    .stButton>button:hover { background-color: #e6c200; color: black; }
    h1, h2, h3, h4, h5, h6 { color: #FFD700 !important; font-family: 'Arial Black', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

st.title("🟨 JANTA DRAMATIC: AI TRADING HOUSE - FINAL")

# --- ACCOUNT GUARD ---
st.sidebar.markdown("<h2 style='color:#FFD700;'>🛡️ ACCOUNT GUARD</h2>", unsafe_allow_html=True)
account_size = st.sidebar.number_input("Account Balance ($)", min_value=10, value=1000)
risk_percent = st.sidebar.slider("Risk Per Trade (%)", 0.5, 3.0, 1.0)
daily_limit = st.sidebar.slider("Daily Drawdown Limit (%)", 1, 5, 4)

# --- PAIRS ---
PAIRS_DICT = {
    "XAUUSD (Gold) - GC=F": "GC=F",
    "BTC-USD (Bitcoin)": "BTC-USD",
    "EURUSD=X (Euro)": "EURUSD=X",
    "GBPUSD=X (Pound)": "GBPUSD=X",
    "USDJPY=X (Yen)": "USDJPY=X",
    "ETH-USD (Ethereum)": "ETH-USD"
}

# --- 90 DAYS LOCAL STORAGE SYSTEM ---
DATA_FOLDER = Path("market_data_store")
DATA_FOLDER.mkdir(exist_ok=True)

def get_local_file_path(ticker, tf):
    safe_ticker = ticker.replace("=", "_").replace("-", "_").replace("/", "_")
    return DATA_FOLDER / f"{safe_ticker}_{tf}.csv"

@st.cache_data(ttl=300) # 5 min tak Yahoo ko call nahi karega
def load_market_data(ticker, tf):
    local_file = get_local_file_path(ticker, tf)
    df_local = pd.DataFrame()

    if local_file.exists():
        try:
            df_local = pd.read_csv(local_file, index_col=0, parse_dates=True)
        except:
            df_local = pd.DataFrame()

    df_new = pd.DataFrame()
    try:
        period = "60d" if tf in ["15m", "1h"] else "1y"
        df_new = yf.download(ticker, period=period, interval=tf, auto_adjust=True, progress=False, threads=False)
        if not df_new.empty and isinstance(df_new.columns, pd.MultiIndex):
            df_new.columns = df_new.columns.get_level_values(0)
    except:
        pass

    if not df_new.empty:
        combined = pd.concat([df_local, df_new])
        combined = combined[~combined.index.duplicated(keep='last')]
        combined = combined.sort_index()
        # Last 90 Days hi rakho
        try:
            combined = combined.last('90D')
        except:
            pass
    else:
        combined = df_local

    if not combined.empty:
        try:
            combined.to_csv(local_file)
        except:
            pass

    return combined

# --- INPUTS ---
col1, col2 = st.columns(2)
with col1:
    selected_label = st.selectbox("Select Pair", list(PAIRS_DICT.keys()))
    symbol = PAIRS_DICT[selected_label]
with col2:
    timeframe = st.selectbox("Select Timeframe", ("15m", "1h", "4h", "1d"))

if st.button("START AI ANALYSIS"):
    with st.spinner("Analyzing 90 Days Deep Data..."):
        df = load_market_data(symbol, timeframe)

        if df.empty or len(df) < 50:
            st.error("Data nahi mila. Yahoo thoda slow hai, 10 sec baad dobara dabao.")
            st.stop()

        closes = df['Close'].astype(float)
        highs = df['High'].astype(float)
        lows = df['Low'].astype(float)
        opens = df['Open'].astype(float)

        ema20 = closes.ewm(span=20, adjust=False).mean()
        ema50 = closes.ewm(span=50).mean()
        
        delta = closes.diff()
        gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / loss.replace(0, 0.001)
        rsi = 100 - (100 / (1 + rs))

        tr = pd.concat([highs - lows, (highs - closes.shift(1)).abs(), (lows - closes.shift(1)).abs()], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1/14, adjust=False).mean()

        score = 50
        reasons = []
        curr_atr = float(atr.iloc[-1])
        last_close = float(closes.iloc[-1])
        curr_ema20 = float(ema20.iloc[-1])
        curr_ema50 = float(ema50.iloc[-1])
        curr_rsi = float(rsi.iloc[-1])

        # 1. Trend - Isse 50-50 khatam hoga
        if last_close > curr_ema20 > curr_ema50:
            score += 15
            reasons.append(f"Strong Bullish Trend: Price > EMA20 > EMA50")
        elif last_close < curr_ema20 < curr_ema50:
            score -= 15
            reasons.append(f"Strong Bearish Trend: Price < EMA20 < EMA50")
        elif last_close > curr_ema50:
            score += 7
            reasons.append(f"Price above EMA50 - Bullish Bias")
        else:
            score -= 7
            reasons.append(f"Price below EMA50 - Bearish Bias")

        if curr_rsi > 58:
            score += 10
            reasons.append(f"RSI Bullish Momentum ({curr_rsi:.1f})")
        elif curr_rsi < 42:
            score -= 10
            reasons.append(f"RSI Bearish Momentum ({curr_rsi:.1f})")

        # 2. FVG
        if float(lows.iloc[-1]) > float(highs.iloc[-3]):
            score += 12
            reasons.append("Bullish FVG - Institutions Buying")
        elif float(highs.iloc[-1]) < float(lows.iloc[-3]):
            score -= 12
            reasons.append("Bearish FVG - Institutions Selling")

        # 3. Wick
        body = abs(float(opens.iloc[-1]) - last_close)
        if body > 0:
            lower_wick = min(float(opens.iloc[-1]), last_close) - float(lows.iloc[-1])
            upper_wick = float(highs.iloc[-1]) - max(float(opens.iloc[-1]), last_close)
            if lower_wick > body * 1.2:
                score += 10
                reasons.append("Lower Wick Rejection - Buyers Active")
            if upper_wick > body * 1.2:
                score -= 10
                reasons.append("Upper Wick Rejection - Sellers Active")

        # 4. BOS
        recent_max = float(highs.iloc[-20:-1].max())
        recent_min = float(lows.iloc[-20:-1].min())
        if last_close > recent_max:
            score += 8
            reasons.append("Bullish BOS - Breaking Recent High")
        elif last_close < recent_min:
            score -= 8
            reasons.append("Bearish BOS - Breaking Recent Low")

        buy_prob = int(max(5, min(95, score)))
        sell_prob = 100 - buy_prob

        m1, m2, m3 = st.columns(3)
        m1.metric("🟢 BUY CHANCE", f"{buy_prob}%")
        m2.metric("🔴 SELL CHANCE", f"{sell_prob}%")
        m3.metric("💾 STORED CANDLES", f"{len(df)} (90D)")

        st.markdown("---")

        entry = last_close
        # FIXED: SL hamesha chhota, TP hamesha bada
        sl_mult = 1.5
        tp_mult = 2.5  # RR = 1 : 1.66 pakka

        if buy_prob >= 60:
            sl = entry - (curr_atr * sl_mult)
            tp = entry + (curr_atr * tp_mult)
            risk = entry - sl
            reward = tp - entry
            st.success(f"🚀 LONG SETUP CONFIRMED - Score {buy_prob}/100 - RR 1:{reward/risk:.2f}")
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<h4 style='color:white;'>ENTRY: {entry:.2f}</h4>", unsafe_allow_html=True)
            c2.markdown(f"<h4 style='color:#FF4B4B;'>🛑 SL: {sl:.2f} (-{risk:.2f})</h4>", unsafe_allow_html=True)
            c3.markdown(f"<h4 style='color:#00E676;'>🎯 TP: {tp:.2f} (+{reward:.2f})</h4>", unsafe_allow_html=True)

        elif sell_prob >= 60:
            sl = entry + (curr_atr * sl_mult)
            tp = entry - (curr_atr * tp_mult)
            risk = sl - entry
            reward = entry - tp
            st.error(f"📉 SHORT SETUP CONFIRMED - Score {sell_prob}/100 - RR 1:{reward/risk:.2f}")
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<h4 style='color:white;'>ENTRY: {entry:.2f}</h4>", unsafe_allow_html=True)
            c2.markdown(f"<h4 style='color:#FF4B4B;'>🛑 SL: {sl:.2f} (+{risk:.2f})</h4>", unsafe_allow_html=True)
            c3.markdown(f"<h4 style='color:#00E676;'>🎯 TP: {tp:.2f} (-{reward:.2f})</h4>", unsafe_allow_html=True)
        else:
            st.info(f"⚖️ WAIT ZONE - Buy {buy_prob}% / Sell {sell_prob}% - Market Balanced")

        with st.expander("📝 SEE AI THESIS"):
            for r in reasons:
                st.write(f"✔️ {r}")

        st.markdown(f"### 📊 Live Chart - {selected_label} ({timeframe}) - {len(df)} Candles Loaded")
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=opens, high=highs, low=lows, close=closes, increasing_line_color='#FFD700', decreasing_line_color='#FF0000')])
        fig.add_trace(go.Scatter(x=df.index, y=ema20, line=dict(color='#FFD700', width=1), name='EMA20'))
        fig.add_trace(go.Scatter(x=df.index, y=ema50, line=dict(color='white', width=1), name='EMA50'))
        fig.update_layout(template="plotly_dark", paper_bgcolor='black', plot_bgcolor='black', xaxis_rangeslider_visible=False, height=550)
        st.plotly_chart(fig, use_container_width=True)

# --- STORAGE STATUS IN SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.markdown("**💾 Local 90D Storage:**")
if DATA_FOLDER.exists():
    for f in sorted(DATA_FOLDER.glob("*.csv")):
        try:
            count = len(pd.read_csv(f))
            st.sidebar.caption(f"{f.name.replace('.csv','')}: {count}")
        except:
            pass
