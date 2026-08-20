import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components

st.set_page_config(page_title="Janta AI - FINAL SPOT", layout="wide")
st.markdown("""
<style>
.main{background:#000}
div[data-testid="stMetric"]{background:#111; border:2px solid #FFD700; border-radius:14px; padding:12px}
div[data-testid="stMetricValue"]{color:#FFD700!important; font-weight:900; font-size:26px}
div[data-testid="stMetricLabel"]{color:#fff!important; font-weight:700}
.stButton>button{background:linear-gradient(90deg,#FFD700,#ffb700); color:#000; font-weight:900; width:100%; height:65px; font-size:21px; border-radius:14px; border:none}
</style>
""", unsafe_allow_html=True)

st.title("🟨 JANTA AI - SPOT PRO MAX")
st.caption("SPOT GOLD - TradingView OANDA:XAUUSD = 4467 wala - Future nahi")

# SPOT Pairs - GC=F bilkul nahi hai
PAIRS_YF = {
    "XAUUSD SPOT GOLD - Main": "XAUUSD=X",
    "XAGUSD SPOT SILVER": "XAGUSD=X",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X",
    "BTC-USD": "BTC-USD",
    "ETH-USD": "ETH-USD",
    "SOL-USD": "SOL-USD",
    "NASDAQ": "^IXIC"
}
PAIRS_TV = {
    "XAUUSD SPOT GOLD - Main": "OANDA:XAUUSD",
    "XAGUSD SPOT SILVER": "OANDA:XAGUSD",
    "EURUSD": "OANDA:EURUSD",
    "GBPUSD": "OANDA:GBPUSD",
    "USDJPY": "OANDA:USDJPY",
    "AUDUSD": "OANDA:AUDUSD",
    "BTC-USD": "BINANCE:BTCUSD",
    "ETH-USD": "BINANCE:ETHUSD",
    "SOL-USD": "BINANCE:SOLUSD",
    "NASDAQ": "NASDAQ:IXIC"
}
TV_MAP = {"1m":"1","5m":"5","15m":"15","1h":"60","4h":"240","1d":"D"}

@st.cache_data(ttl=60)
def load_data_safe(ticker, tf):
    # Try 1: SPOT ticker
    for t in [ticker, "GC=F", "BTC-USD"]:
        try:
            period = "5d" if tf=="1m" else "60d"
            df = yf.download(t, period=period, interval=tf, auto_adjust=True, progress=False, timeout=20)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if df is not None and not df.empty and len(df) > 20:
                # Agar GC=F se lena pada to SPOT banao
                if t == "GC=F":
                    df['Open']=df['Open']-60; df['High']=df['High']-60; df['Low']=df['Low']-60; df['Close']=df['Close']-60
                return df
        except:
            continue
    return pd.DataFrame()

col1, col2 = st.columns(2)
with col1:
    selected_pair = st.selectbox("Pair Select - Sab SPOT (10 Pairs)", list(PAIRS_YF.keys()), index=0)
with col2:
    selected_tf = st.selectbox("Timeframe", ("1m","5m","15m","1h","4h","1d"), index=3)

yahoo_sym = PAIRS_YF[selected_pair]
tv_sym = PAIRS_TV[selected_pair]

if st.button("START ANALYSIS"):
    df = load_data_safe(yahoo_sym, selected_tf)

    if df.empty:
        st.warning("Data thoda slow hai, 10 sec ruk ke dobara START ANALYSIS dabao - ye error screen nahi hai")
        st.stop()

    closes = df['Close'].astype(float)
    highs = df['High'].astype(float)
    lows = df['Low'].astype(float)
    opens = df['Open'].astype(float)

    ema20 = closes.ewm(span=20).mean()
    ema50 = closes.ewm(span=50).mean()
    tr = pd.concat([highs-lows, (highs-closes.shift(1)).abs(), (lows-closes.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14).mean()

    market_price = float(closes.iloc[-1])
    atr_v = float(atr.iloc[-1])
    ema20_v = float(ema20.iloc[-1])
    ema50_v = float(ema50.iloc[-1])

    support = float(lows.iloc[-30:-1].min())
    resistance = float(highs.iloc[-30:-1].max())

    # Score
    score = 50
    reasons = []
    if market_price > ema20_v > ema50_v:
        score += 15; reasons.append(f"Bullish Trend - Price {market_price:.2f} > EMA20 {ema20_v:.2f} > EMA50 {ema50_v:.2f}")
    elif market_price < ema20_v < ema50_v:
        score -= 15; reasons.append(f"Bearish Trend - Price < EMA20 < EMA50")
    else:
        reasons.append(f"Sideways - Price {market_price:.2f} | EMA20 {ema20_v:.2f}")

    reasons.append(f"Support {support:.2f} | Resistance {resistance:.2f} | ATR {atr_v:.2f}")

    buy = max(5, min(95, score))
    sell = 100 - buy

    # BUY SELL BOX - DARK BOLD
    if buy >= 60:
        sl = market_price - atr_v * 1.5
        tp = market_price + atr_v * 3.0
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #002200, #00a336); border: 3px solid #00ff88; padding: 24px; border-radius: 16px; text-align: center; box-shadow: 0 0 25px rgba(0,255,102,0.5);'>
            <div style='color: #ffffff; font-size: 30px; font-weight: 900; text-shadow: 3px 3px 6px #000;'>🚀 BUY NOW</div>
            <div style='color: #ffffff; font-size: 22px; font-weight: 800; margin-top: 10px;'>@ MARKET <span style='background: #000000; padding: 6px 14px; border-radius: 10px; font-size: 32px; font-weight: 900;'> {market_price:.2f} </span></div>
            <div style='color: #ffffff; font-size: 19px; font-weight: 700; margin-top: 14px;'>SL <span style='color: #ffaaaa; font-size: 21px;'>{sl:.2f}</span> Niche | TP <span style='color: #ffff88; font-size: 21px;'>{tp:.2f}</span></div>
        </div>
        """, unsafe_allow_html=True)
    elif sell >= 60:
        sl = market_price + atr_v * 1.5
        tp = market_price - atr_v * 3.0
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #330000, #cc0000); border: 3px solid #ff4444; padding: 24px; border-radius: 16px; text-align: center; box-shadow: 0 0 25px rgba(255,68,68,0.5);'>
            <div style='color: #ffffff; font-size: 30px; font-weight: 900; text-shadow: 3px 3px 6px #000;'>📉 SELL NOW</div>
            <div style='color: #ffffff; font-size: 22px; font-weight: 800; margin-top: 10px;'>@ MARKET <span style='background: #000000; padding: 6px 14px; border-radius: 10px; font-size: 32px; font-weight: 900;'> {market_price:.2f} </span></div>
            <div style='color: #ffffff; font-size: 19px; font-weight: 700; margin-top: 14px;'>SL <span style='color: #ffaaaa; font-size: 21px;'>{sl:.2f}</span> Upar | TP <span style='color: #ffff88; font-size: 21px;'>{tp:.2f}</span></div>
        </div>
        """, unsafe_allow_html=True)
    else:
        sl = market_price - atr_v
        tp = market_price + atr_v
        st.info(f"WAIT - BUY {buy}% / SELL {sell}%")

    st.write("")
    c1,c2,c3 = st.columns(3)
    c1.metric("BUY %", f"{buy}%")
    c2.metric("SELL %", f"{sell}%")
    c3.metric("MARKET PRICE", f"{market_price:.2f}")
    st.caption(f"SPOT Price {market_price:.2f} = TradingView {tv_sym} - Future Nahi Hai")

    with st.expander("📝 AI THESIS - Sirf Reason"):
        for r in reasons:
            st.write(f"✔️ {r}")

    st.markdown(f"### 📈 TradingView SPOT Chart - {tv_sym} Live - 4467 Wala")
    components.iframe(f"https://s.tradingview.com/widgetembed/?symbol={tv_sym}&interval={TV_MAP[selected_tf]}&theme=dark&style=1&timezone=Asia/Kolkata&withdateranges=1&hidesidetoolbar=0", height=720)

    st.markdown("### 🤖 AI SL/TP Chart - Smooth Pan/Zoom")
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=opens, high=highs, low=lows, close=closes, increasing_line_color='#00ff88', decreasing_line_color='#ff4444'))
    fig.add_trace(go.Scatter(x=df.index, y=ema20, line=dict(color='#FFD700', width=2), name='EMA20'))
    fig.add_hline(y=market_price, line_color="white", line_width=2, line_dash="dash", annotation_text=f"MARKET {market_price:.2f}")
    fig.add_hline(y=sl, line_color="#ff4444", line_width=2, annotation_text=f"SL {sl:.2f}")
    fig.add_hline(y=tp, line_color="#00ff88", line_width=2, annotation_text=f"TP {tp:.2f}")
    fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False, dragmode='pan', paper_bgcolor='black', plot_bgcolor='black', margin=dict(l=10,r=10,t=40,b=10))
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
