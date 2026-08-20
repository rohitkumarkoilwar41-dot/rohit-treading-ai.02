import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Janta AI Trading House", layout="wide")
st.markdown("""
    <style>
   .main { background-color: #000000; color: #FFD700; }
   .stMetric { background-color: #1a1a1a; border: 2px solid #FFD700; border-radius: 12px; padding: 15px; }
    div[data-testid="stMetricValue"] { color: #FFD700!important; font-weight: bold; }
   .stButton>button { background-color: #FFD700; color: black; font-weight: 900; border-radius: 8px; width: 100%; height: 50px; font-size: 18px; border: none; }
    h1, h2, h3 { color: #FFD700!important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🟨 JANTA DRAMATIC: AI TRADING HOUSE - OB SL")

st.sidebar.markdown("<h2 style='color:#FFD700;'>🛡️ ACCOUNT GUARD</h2>", unsafe_allow_html=True)
account_size = st.sidebar.number_input("Account Balance ($)", min_value=10, value=1000)

PAIRS_DICT = {
    "XAUUSD (Gold) - GC=F": "GC=F",
    "BTC-USD (Bitcoin)": "BTC-USD",
    "EURUSD=X (Euro)": "EURUSD=X",
    "GBPUSD=X (Pound)": "GBPUSD=X",
    "USDJPY=X (Yen)": "USDJPY=X",
    "ETH-USD (Ethereum)": "ETH-USD"
}

DATA_FOLDER = Path("market_data_store")
DATA_FOLDER.mkdir(exist_ok=True)

def get_local_file_path(ticker, tf):
    safe = ticker.replace("=", "_").replace("-", "_")
    return DATA_FOLDER / f"{safe}_{tf}.csv"

@st.cache_data(ttl=300)
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
        combined = combined[~combined.index.duplicated(keep='last')].sort_index()
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

def find_order_blocks(df, lookback=40):
    bullish_obs = []
    bearish_obs = []
    recent = df.tail(lookback)
    closes = recent['Close'].astype(float)
    opens = recent['Open'].astype(float)
    highs = recent['High'].astype(float)
    lows = recent['Low'].astype(float)
    for i in range(1, len(recent)-3):
        curr_close = float(closes.iloc[i])
        curr_open = float(opens.iloc[i])
        if curr_close < curr_open: # Red candle
            if i+2 < len(closes) and float(closes.iloc[i+1]) > float(opens.iloc[i+1]) and float(closes.iloc[i+2]) > float(highs.iloc[i]):
                bullish_obs.append((float(highs.iloc[i]), float(lows.iloc[i]), recent.index[i]))
        if curr_close > curr_open: # Green candle
            if i+2 < len(closes) and float(closes.iloc[i+1]) < float(opens.iloc[i+1]) and float(closes.iloc[i+2]) < float(lows.iloc[i]):
                bearish_obs.append((float(highs.iloc[i]), float(lows.iloc[i]), recent.index[i]))
    return bullish_obs, bearish_obs

col1, col2 = st.columns(2)
with col1:
    selected_label = st.selectbox("Select Pair", list(PAIRS_DICT.keys()))
    symbol = PAIRS_DICT[selected_label]
with col2:
    timeframe = st.selectbox("Select Timeframe", ("15m", "1h", "4h", "1d"))

if st.button("START AI ANALYSIS"):
    with st.spinner("Analyzing Order Blocks..."):
        df = load_market_data(symbol, timeframe)
        if df.empty or len(df) < 50:
            st.error("Data slow hai, dobara try karo.")
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
        last_close = float(closes.iloc[-1])
        curr_ema20 = float(ema20.iloc[-1])
        curr_ema50 = float(ema50.iloc[-1])
        curr_rsi = float(rsi.iloc[-1])
        curr_atr = float(atr.iloc[-1])

        if last_close > curr_ema20 > curr_ema50:
            score += 15
            reasons.append(f"Strong Bullish Trend: Price > EMA20 > EMA50")
        elif last_close < curr_ema20 < curr_ema50:
            score -= 15
            reasons.append(f"Strong Bearish Trend: Price < EMA20 < EMA50")

        if curr_rsi > 58:
            score += 10
            reasons.append(f"RSI Bullish ({curr_rsi:.1f})")
        elif curr_rsi < 42:
            score -= 10
            reasons.append(f"RSI Bearish ({curr_rsi:.1f})")

        if float(lows.iloc[-1]) > float(highs.iloc[-3]):
            score += 12
            reasons.append("Bullish FVG")
        elif float(highs.iloc[-1]) < float(lows.iloc[-3]):
            score -= 12
            reasons.append("Bearish FVG")

        buy_prob = int(max(5, min(95, score)))
        sell_prob = 100 - buy_prob

        m1, m2, m3 = st.columns(3)
        m1.metric("🟢 BUY", f"{buy_prob}%")
        m2.metric("🔴 SELL", f"{sell_prob}%")
        m3.metric("💾 DATA", f"{len(df)}")

        bullish_obs, bearish_obs = find_order_blocks(df)
        entry = last_close

        if buy_prob >= 60:
            sl = None
            sl_reason = ""
            valid_obs = [ob for ob in bullish_obs if ob[1] < entry]
            if valid_obs:
                nearest = valid_obs[-1]
                sl = nearest[1] - (curr_atr * 0.2)
                sl_reason = f"Bullish OB {nearest[1]:.2f}-{nearest[0]:.2f} ke neeche"
            if sl is None:
                prot_low = float(lows.iloc[-7:-1].min())
                sl = prot_low - (curr_atr * 0.2)
                sl_reason = f"Protected Low {prot_low:.2f} ke neeche"

            tp = float(highs.iloc[-20:-1].max())
            risk = entry - sl
            reward = tp - entry
            if risk >= reward:
                tp = float(highs.max())
                reward = tp - entry

            if risk > 0 and reward > 0 and risk < reward:
                st.success(f"🚀 LONG | RR 1:{reward/risk:.2f} | SL Logic se")
                st.markdown(f"**ENTRY {entry:.2f} | SL {sl:.2f} | TP {tp:.2f}**")
                st.caption(f"SL: {sl_reason} | TP: Next Liquidity {tp:.2f}")
            else:
                st.warning("Trade Skip - SL TP se bada hai, WAIT")

        elif sell_prob >= 60:
            sl = None
            valid_obs = [ob for ob in bearish_obs if ob[0] > entry]
            if valid_obs:
                nearest = valid_obs[-1]
                sl = nearest[0] + (curr_atr * 0.2)
                sl_reason = f"Bearish OB {nearest[1]:.2f}-{nearest[0]:.2f} ke upar"
            if sl is None:
                prot_high = float(highs.iloc[-7:-1].max())
                sl = prot_high + (curr_atr * 0.2)
                sl_reason = f"Protected High {prot_high:.2f} ke upar"

            tp = float(lows.iloc[-20:-1].min())
            risk = sl - entry
            reward = entry - tp
            if risk >= reward:
                tp = float(lows.min())
                reward = entry - tp

            if risk > 0 and reward > 0 and risk < reward:
                st.error(f"📉 SHORT | RR 1:{reward/risk:.2f} | SL Logic se")
                st.markdown(f"**ENTRY {entry:.2f} | SL {sl:.2f} | TP {tp:.2f}**")
                st.caption(f"SL: {sl_reason} | TP: Next Liquidity {tp:.2f}")
            else:
                st.warning("Trade Skip - SL TP se bada hai, WAIT")
        else:
            st.info(f"WAIT - Buy {buy_prob}% / Sell {sell_prob}%")

        with st.expander("📝 AI THESIS"):
            for r in reasons:
                st.write(f"✔️ {r}")
            st.write(f"OB Found: {len(bullish_obs)} Bullish, {len(bearish_obs)} Bearish")

        fig = go.Figure(data=[go.Candlestick(x=df.index, open=opens, high=highs, low=lows, close=closes, increasing_line_color='#FFD700', decreasing_line_color='#FF0000')])
        fig.add_trace(go.Scatter(x=df.index, y=ema20, line=dict(color='#FFD700', width=1), name='EMA20'))
        fig.add_trace(go.Scatter(x=df.index, y=ema50, line=dict(color='white', width=1), name='EMA50'))
        fig.update_layout(template="plotly_dark", paper_bgcolor='black', plot_bgcolor='black', xaxis_rangeslider_visible=False, height=550)
        st.plotly_chart(fig, use_container_width=True)
