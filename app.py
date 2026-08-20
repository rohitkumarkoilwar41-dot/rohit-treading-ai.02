import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import streamlit.components.v1 as components

st.set_page_config(page_title="Janta AI - Pro Max", layout="wide")
st.markdown("""
<style>
.main { background-color: #000000; }
.stMetric { background-color: #111; border: 2px solid #FFD700; border-radius: 12px; }
div[data-testid="stMetricValue"] { color: #FFD700!important; }
.stButton>button { background-color: #FFD700; color: black; font-weight: 900; width: 100%; height: 55px; font-size: 18px; margin-top: 15px; }
</style>
""", unsafe_allow_html=True)

st.title("🟨 JANTA AI - PRO MAX")

TV_MAP = {"1m":"1", "5m":"5", "15m":"15", "1h":"60", "4h":"240", "1d":"D"}

# 1. AUR PAIRS ADD KIYA - SAB SPOT WALA NAAM
PAIRS_YF = {
    "XAUUSD SPOT GOLD": "GC=F",
    "XAGUSD SPOT SILVER": "SI=F",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "BTC-USD": "BTC-USD",
    "ETH-USD": "ETH-USD",
    "NASDAQ": "^IXIC"
}
# TradingView ke liye alag symbol
PAIRS_TV = {
    "XAUUSD SPOT GOLD": "OANDA:XAUUSD",
    "XAGUSD SPOT SILVER": "OANDA:XAGUSD",
    "EURUSD": "OANDA:EURUSD",
    "GBPUSD": "OANDA:GBPUSD",
    "USDJPY": "OANDA:USDJPY",
    "BTC-USD": "BINANCE:BTCUSD",
    "ETH-USD": "BINANCE:ETHUSD",
    "NASDAQ": "NASDAQ:IXIC"
}

DATA_FOLDER = Path("market_data_store"); DATA_FOLDER.mkdir(exist_ok=True)
def get_path(t, tf): return DATA_FOLDER / f"{t.replace('=','_')}_{tf}.csv"

@st.cache_data(ttl=300)
def load_data(ticker, tf):
    f = get_path(ticker, tf)
    df_old = pd.read_csv(f, index_col=0, parse_dates=True) if f.exists() else pd.DataFrame()
    try:
        period = "7d" if tf=="1m" else "60d" if tf in ["5m","15m","1h"] else "1y"
        df_new = yf.download(ticker, period=period, interval=tf, auto_adjust=True, progress=False)
        if isinstance(df_new.columns, pd.MultiIndex): df_new.columns = df_new.columns.get_level_values(0)
    except: df_new = pd.DataFrame()
    if not df_new.empty:
        combined = pd.concat([df_old, df_new]); combined = combined[~combined.index.duplicated(keep='last')].sort_index().tail(500)
        combined.to_csv(f); return combined
    return df_old

c1, c2 = st.columns(2)
with c1:
    # Index 0 = GOLD SPOT hi default rahega
    pair_name = st.selectbox("Pair Select - Sab SPOT hai", list(PAIRS_YF.keys()), index=0)
with c2:
    tf = st.selectbox("Timeframe", ("1m","5m","15m","1h","4h","1d"), index=2)

symbol_yf = PAIRS_YF[pair_name]
symbol_tv = PAIRS_TV[pair_name]

if st.button("START ANALYSIS"):
    df = load_data(symbol_yf, tf)
    if df.empty or len(df) < 30:
        st.error("Data slow hai, dobara dabao"); st.stop()

    closes, highs, lows, opens = df['Close'].astype(float), df['High'].astype(float), df['Low'].astype(float), df['Open'].astype(float)
    ema20, ema50 = closes.ewm(span=20).mean(), closes.ewm(span=50).mean()
    rsi = 100 - (100/(1+ (closes.diff().clip(lower=0).ewm(alpha=1/14).mean() / (-closes.diff().clip(upper=0)).ewm(alpha=1/14).mean().replace(0,0.001))))
    atr = pd.concat([highs-lows, (highs-closes.shift(1)).abs(), (lows-closes.shift(1)).abs()], axis=1).max(axis=1).ewm(alpha=1/14).mean()

    last, e20, e50, rsi_v, atr_v = float(closes.iloc[-1]), float(ema20.iloc[-1]), float(ema50.iloc[-1]), float(rsi.iloc[-1]), float(atr.iloc[-1])
    support, resistance = float(lows.iloc[-20:-1].min()), float(highs.iloc[-20:-1].max())

    score=50; reasons=[]
    if last > e20 > e50: score+=15; reasons.append(f"BOS Bullish - Price > EMA20 > EMA50")
    elif last < e20 < e50: score-=15; reasons.append(f"BOS Bearish")
    if rsi_v>58: score+=10; reasons.append(f"RSI Bullish {rsi_v:.1f}")
    elif rsi_v<42: score-=10; reasons.append(f"RSI Bearish {rsi_v:.1f}")
    reasons.append(f"Support {support:.2f} | Resistance {resistance:.2f}")

    buy = max(5,min(95,score)); sell=100-buy
    entry=last

    # --- GREEN BOX - SIRF UPAR, THESIS ME BILKUL NAHI ---
    if buy>=60:
        sl = support - atr_v*0.3; tp = float(highs.max())
        st.success(f"🚀 LONG | ENTRY {entry:.2f} | SL {sl:.2f} | TP {tp:.2f}")
    elif sell>=60:
        sl = resistance + atr_v*0.3; tp = float(lows.min())
        st.error(f"📉 SHORT | ENTRY {entry:.2f} | SL {sl:.2f} | TP {tp:.2f}")
    else:
        sl, tp = entry-atr_v, entry+atr_v
        st.info(f"WAIT - BUY {buy}% / SELL {sell}%")

    m1,m2,m3 = st.columns(3)
    m1.metric("BUY %", f"{buy}%"); m2.metric("SELL %", f"{sell}%"); m3.metric("PRICE", f"{last:.2f}")

    # Thesis me ENTRY/SL/TP nahi hai - sirf reason
    with st.expander("📝 AI THESIS - Sirf Reason"):
        for r in reasons: st.write(f"✔️ {r}")

    # --- TRADINGVIEW WITH LIVE COUNTDOWN TIMER ---
    st.markdown("### 📈 SPOT Chart - Live Countdown ke saath")
    tv_interval = TV_MAP[tf]
    # Ye wala Advanced Chart hai, isme neeche countdown timer aata hai jo ghat-te rehta hai
    tv_url = f"https://s.tradingview.com/widgetembed/?frameElementId=tradingview_123&symbol={symbol_tv}&interval={tv_interval}&hidesidetoolbar=0&symboledit=1&saveimage=1&toolbarbg=rgba(0,0,0,1)&studies=EMA%40tv-basicstudies%1ARSI%40tv-basicstudies%1AVolume%40tv-basicstudies&theme=dark&style=1&timezone=Asia%2FKolkata&withdateranges=1&showpopupbutton=1"
    components.iframe(tv_url, height=650, scrolling=False)

    # --- SL/TP CHART - TRADINGVIEW JAISA SMOOTH ---
    st.markdown("### 🤖 AI SL/TP Chart - Smooth Pan & Zoom")
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=opens, high=highs, low=lows, close=closes, name="Price"))
    fig.add_trace(go.Scatter(x=df.index, y=ema20, line=dict(color='gold', width=1.5), name='EMA20'))
    fig.add_trace(go.Scatter(x=df.index, y=ema50, line=dict(color='white', width=1), name='EMA50'))
    fig.add_hline(y=entry, line_color="white", line_dash="dash", annotation_text="ENTRY")
    fig.add_hline(y=sl, line_color="red", line_dash="dash", annotation_text="SL")
    fig.add_hline(y=tp, line_color="green", line_dash="dash", annotation_text="TP")

    fig.update_layout(
        template="plotly_dark", height=650,
        xaxis_rangeslider_visible=False,
        dragmode='pan', # Ab mouse se pakad ke idhar-udhar kheech sakte ho
        paper_bgcolor='black', plot_bgcolor='black'
    )
    # Zoom, pan, autoscale ke icons upar sahi jagah pe ayenge
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True, 'modeBarButtonsToRemove': ['select2d','lasso2d']})
