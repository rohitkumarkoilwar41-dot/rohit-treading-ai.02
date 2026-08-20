import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import streamlit.components.v1 as components

st.set_page_config(page_title="Janta AI - Final", layout="wide")
st.markdown("""
    <style>
   .main { background-color: #000000; color: #FFD700; }
   .stMetric { background-color: #1a1a1a; border: 2px solid #FFD700; border-radius: 12px; padding: 15px; }
    div[data-testid="stMetricValue"] { color: #FFD700!important; font-weight: bold; }
   .stButton>button { background-color: #FFD700; color: black; font-weight: 900; border-radius: 8px; width: 100%; height: 55px; font-size: 19px; border: none; }
    h1, h2, h3 { color: #FFD700!important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🟨 JANTA AI - FINAL")

TV_MAP = {"1m":"1", "5m":"5", "15m":"15", "1h":"60", "4h":"240", "1d":"D"}
PAIRS = {"GOLD (GC=F) - AI ke liye": "GC=F", "BTC-USD": "BTC-USD", "EURUSD=X": "EURUSD=X"}

DATA_FOLDER = Path("market_data_store")
DATA_FOLDER.mkdir(exist_ok=True)

def get_path(t, tf): return DATA_FOLDER / f"{t.replace('=','_').replace('-','_')}_{tf}.csv"

@st.cache_data(ttl=600)
def load_data(ticker, tf):
    f = get_path(ticker, tf)
    df_old = pd.read_csv(f, index_col=0, parse_dates=True) if f.exists() else pd.DataFrame()
    try:
        period = "7d" if tf=="1m" else "60d" if tf in ["5m","15m","1h"] else "1y"
        df_new = yf.download(ticker, period=period, interval=tf, auto_adjust=True, progress=False)
        if isinstance(df_new.columns, pd.MultiIndex): df_new.columns = df_new.columns.get_level_values(0)
    except: df_new = pd.DataFrame()
    if not df_new.empty:
        combined = pd.concat([df_old, df_new])
        combined = combined[~combined.index.duplicated(keep='last')].sort_index().tail(500)
        combined.to_csv(f)
        return combined
    return df_old

def find_obs(df):
    bull, bear = [], []
    d = df.tail(50)
    for i in range(1, len(d)-3):
        if float(d['Close'].iloc[i]) < float(d['Open'].iloc[i]):
            if float(d['Close'].iloc[i+1]) > float(d['Open'].iloc[i+1]) and float(d['Close'].iloc[i+2]) > float(d['High'].iloc[i]):
                bull.append((float(d['High'].iloc[i]), float(d['Low'].iloc[i]), d.index[i]))
        if float(d['Close'].iloc[i]) > float(d['Open'].iloc[i]):
            if float(d['Close'].iloc[i+1]) < float(d['Open'].iloc[i+1]) and float(d['Close'].iloc[i+2]) < float(d['Low'].iloc[i]):
                bear.append((float(d['High'].iloc[i]), float(d['Low'].iloc[i]), d.index[i]))
    return bull, bear

c1, c2 = st.columns(2)
with c1: sym_label = st.selectbox("AI Pair", list(PAIRS.keys())); symbol = PAIRS[sym_label]
with c2: tf = st.selectbox("Timeframe", ("1m","5m","15m","1h","4h","1d"), index=2)

if st.button("START ANALYSIS"):
    df = load_data(symbol, tf)
    if df.empty or len(df) < 40:
        st.error("Data slow hai, thodi der me try karo"); st.stop()

    closes, highs, lows, opens = df['Close'].astype(float), df['High'].astype(float), df['Low'].astype(float), df['Open'].astype(float)
    ema20, ema50 = closes.ewm(span=20).mean(), closes.ewm(span=50).mean()
    delta = closes.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14).mean()
    rsi = 100 - (100/(1+gain/loss.replace(0,0.001)))
    tr = pd.concat([highs-lows, (highs-closes.shift(1)).abs(), (lows-closes.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14).mean()

    last, e20, e50, rsi_v, atr_v = float(closes.iloc[-1]), float(ema20.iloc[-1]), float(ema50.iloc[-1]), float(rsi.iloc[-1]), float(atr.iloc[-1])
    support, resistance = float(lows.iloc[-20:-1].min()), float(highs.iloc[-20:-1].max())
    last_high, last_low = float(highs.iloc[-10:-1].max()), float(lows.iloc[-10:-1].min())

    score, reasons = 50, []
    reasons.append(f"Support: {support:.2f} | Resistance: {resistance:.2f}")

    if last > e20 > e50:
        score+=15; reasons.append(f"BOS Bullish: Price > EMA20 > EMA50 (Last High {last_high:.2f} toda)")
    elif last < e20 < e50:
        score-=15; reasons.append(f"BOS Bearish: Price < EMA20 < EMA50")

    if float(ema20.iloc[-5]) < float(ema50.iloc[-5]) and e20 > e50:
        score+=12; reasons.append("CHOCH: Bearish se Bullish me badla")
    elif float(ema20.iloc[-5]) > float(ema50.iloc[-5]) and e20 < e50:
        score-=12; reasons.append("CHOCH: Bullish se Bearish me badla")

    if rsi_v>58: score+=10; reasons.append(f"RSI Bullish {rsi_v:.1f}")
    elif rsi_v<42: score-=10; reasons.append(f"RSI Bearish {rsi_v:.1f}")

    if float(lows.iloc[-1]) > float(highs.iloc[-3]): score+=8; reasons.append(f"Bullish FVG Gap")
    elif float(highs.iloc[-1]) < float(lows.iloc[-3]): score-=8; reasons.append(f"Bearish FVG Gap")

    b_obs, be_obs = find_obs(df)
    reasons.append(f"Order Blocks: {len(b_obs)} Bullish, {len(be_obs)} Bearish")
    buy, sell = max(5,min(95,score)), 100-max(5,min(95,score))

    m1,m2,m3 = st.columns(3)
    m1.metric("BUY %", f"{buy}%"); m2.metric("SELL %", f"{sell}%"); m3.metric("AI PRICE", f"{last:.2f}")

    entry = last
    # SL TP
    if buy >= 60:
        valid = [o for o in b_obs if o[1] < entry]
        sl = valid[-1][1] - atr_v*0.2 if valid else support - atr_v*0.3
        tp = float(highs.max())
        rr = (tp-entry)/(entry-sl) if entry>sl else 0
        if rr>1: st.success(f"🚀 LONG | ENTRY {entry:.2f} | SL {sl:.2f} | TP {tp:.2f} | RR 1:{rr:.2f}")
        else: st.warning("WAIT - RR sahi nahi")
    elif sell >= 60:
        valid = [o for o in be_obs if o[0] > entry]
        sl = valid[-1][0] + atr_v*0.2 if valid else resistance + atr_v*0.3
        tp = float(lows.min())
        rr = (entry-tp)/(sl-entry) if sl>entry else 0
        if rr>1: st.error(f"📉 SHORT | ENTRY {entry:.2f} | SL {sl:.2f} | TP {tp:.2f} | RR 1:{rr:.2f}")
        else: st.warning("WAIT - RR sahi nahi")
    else:
        st.info(f"WAIT - {buy}% BUY / {sell}% SELL"); sl, tp = entry-atr_v, entry+atr_v

    with st.expander("📝 AI THESIS - Sab Kuch"):
        for r in reasons: st.write(f"✔️ {r}")

    # TradingView Chart - Permanent History
    st.markdown("### 📈 TradingView Chart (OANDA:XAUUSD SPOT) - History kabhi nahi hattega")
    tv_interval = TV_MAP[tf]
    tv_html = f"""
    <div class="tradingview-widget-container"><div id="tv" style="height:600px;"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({{"autosize":true,"symbol":"OANDA:XAUUSD","interval":"{tv_interval}","timezone":"Asia/Kolkata","theme":"dark","style":"1","locale":"in","allow_symbol_change":true,"container_id":"tv","studies":["EMA@tv-basicstudies","RSI@tv-basicstudies"]}});
    </script></div>
    """
    components.html(tv_html, height=620)

    # AI Chart with SL/TP lines
    st.markdown("### 🤖 AI SL/TP Chart")
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=opens, high=highs, low=lows, close=closes, increasing_line_color='#FFD700', decreasing_line_color='#FF0000')])
    fig.add_trace(go.Scatter(x=df.index, y=ema20, line=dict(color='#FFD700', width=1), name='EMA20'))
    fig.add_trace(go.Scatter(x=df.index, y=ema50, line=dict(color='white', width=1), name='EMA50'))
    fig.add_hline(y=entry, line_dash="dash", line_color="white", annotation_text=f"ENTRY {entry:.2f}")
    fig.add_hline(y=sl, line_dash="dash", line_color="red", annotation_text=f"SL {sl:.2f}")
    fig.add_hline(y=tp, line_dash="dash", line_color="green", annotation_text=f"TP {tp:.2f}")
    fig.add_hline(y=support, line_dash="dot", line_color="#00ff00", annotation_text=f"SUP {support:.2f}")
    fig.add_hline(y=resistance, line_dash="dot", line_color="#ff0000", annotation_text=f"RES {resistance:.2f}")
    fig.update_layout(template="plotly_dark", paper_bgcolor='black', plot_bgcolor='black', xaxis_rangeslider_visible=False, height=500)
    st.plotly_chart(fig, use_container_width=True)
