import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import streamlit.components.v1 as components

# ================= PAGE SETUP =================
st.set_page_config(page_title="Janta AI - Pro SPOT", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.main { background-color: #000000; }
div[data-testid="stMetric"] { background: #111111; border: 2px solid #FFD700; border-radius: 14px; padding: 10px; }
div[data-testid="stMetricValue"] { color: #FFD700 !important; font-weight: 900; font-size: 28px; }
div[data-testid="stMetricLabel"] { color: #ffffff !important; font-weight: 700; }
.stButton>button { background: linear-gradient(90deg, #FFD700, #ffb700); color: #000000; font-weight: 900; width: 100%; height: 62px; font-size: 20px; border-radius: 12px; border: none; letter-spacing: 1px; }
.stSelectbox label { color: #FFD700 !important; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

st.title("🟨 JANTA AI - SPOT PRO MAX")
st.caption("TradingView OANDA:XAUUSD SPOT Data | MARKET PRICE se hi BUY/SELL")

# ================= PAIRS - SIRF SPOT =================
PAIRS_YF = {
    "XAUUSD SPOT GOLD - Main": "XAUUSD=X",
    "XAGUSD SPOT SILVER": "XAGUSD=X",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCHF": "USDCHF=X",
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
    "USDCHF": "OANDA:USDCHF",
    "BTC-USD": "BINANCE:BTCUSD",
    "ETH-USD": "BINANCE:ETHUSD",
    "SOL-USD": "BINANCE:SOLUSD",
    "NASDAQ": "NASDAQ:IXIC"
}

TV_INTERVAL = {"1m":"1", "5m":"5", "15m":"15", "1h":"60", "4h":"240", "1d":"D"}

# ================= DATA LOADING - SIRF SPOT =================
@st.cache_data(ttl=30)
def load_spot_data(ticker, timeframe):
    try:
        period = "7d" if timeframe == "1m" else "60d" if timeframe in ["5m","15m","1h"] else "1y"
        df = yf.download(ticker, period=period, interval=timeframe, auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if not df.empty:
            df = df.dropna().tail(500)
            return df
    except Exception as e:
        st.write(f"Error: {e}")
    return pd.DataFrame()

# ================= UI =================
col1, col2 = st.columns(2)
with col1:
    selected_pair = st.selectbox("Pair Select - Sab SPOT Hai (11 Pairs)", list(PAIRS_YF.keys()), index=0)
with col2:
    selected_tf = st.selectbox("Timeframe", ("1m","5m","15m","1h","4h","1d"), index=3)

yahoo_symbol = PAIRS_YF[selected_pair]
tradingview_symbol = PAIRS_TV[selected_pair]

# ================= ANALYSIS =================
if st.button("START ANALYSIS"):
    df = load_spot_data(yahoo_symbol, selected_tf)

    if df.empty or len(df) < 30:
        st.error(f"{yahoo_symbol} ka SPOT data load ho raha hai, 10 second ruk ke dobara START ANALYSIS dabao. Yahoo thoda slow hai.")
        st.stop()

    closes = df['Close'].astype(float)
    highs = df['High'].astype(float)
    lows = df['Low'].astype(float)
    opens = df['Open'].astype(float)

    ema20 = closes.ewm(span=20).mean()
    ema50 = closes.ewm(span=50).mean()
    # RSI
    delta = closes.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14).mean()
    rs = gain / loss.replace(0, 0.001)
    rsi = 100 - (100 / (1 + rs))
    # ATR
    tr = pd.concat([highs-lows, (highs-closes.shift(1)).abs(), (lows-closes.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14).mean()

    last_price = float(closes.iloc[-1])
    last_ema20 = float(ema20.iloc[-1])
    last_ema50 = float(ema50.iloc[-1])
    last_rsi = float(rsi.iloc[-1])
    last_atr = float(atr.iloc[-1])

    support = float(lows.iloc[-30:-1].min())
    resistance = float(highs.iloc[-30:-1].max())
    market_price = last_price  # Jaha market chal raha hai wahi entry

    # BUY/SELL Logic
    score = 50
    reasons = []
    if last_price > last_ema20 > last_ema50:
        score += 15; reasons.append(f"BOS Bullish - Price {last_price:.2f} > EMA20 {last_ema20:.2f} > EMA50 {last_ema50:.2f}")
    elif last_price < last_ema20 < last_ema50:
        score -= 15; reasons.append(f"BOS Bearish - Price < EMA20 < EMA50")
    else:
        reasons.append(f"Sideways - Price {last_price:.2f} | EMA20 {last_ema20:.2f}")

    if last_rsi > 58: score += 10; reasons.append(f"RSI Bullish {last_rsi:.1f}")
    elif last_rsi < 42: score -= 10; reasons.append(f"RSI Bearish {last_rsi:.1f}")
    else: reasons.append(f"RSI Neutral {last_rsi:.1f}")

    reasons.append(f"Support Level {support:.2f} | Resistance {resistance:.2f}")
    reasons.append(f"ATR {last_atr:.2f} - Volatility")

    buy_percent = max(5, min(95, score))
    sell_percent = 100 - buy_percent

    # ================= GREEN / RED BOX - MARKET PRICE SE =================
    if buy_percent >= 60:
        stop_loss = market_price - last_atr * 1.5
        take_profit = market_price + last_atr * 3.0
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #001a00 0%, #006600 50%, #00b33c 100%); border: 3px solid #00ff66; padding: 22px; border-radius: 16px; text-align: center; box-shadow: 0 0 20px rgba(0,255,102,0.4);'>
            <div style='color: #ffffff; font-size: 28px; font-weight: 900; text-transform: uppercase; letter-spacing: 1.5px; text-shadow: 3px 3px 6px #000000;'>🚀 BUY NOW</div>
            <div style='color: #e6ffe6; font-size: 20px; font-weight: 800; margin-top: 10px;'>@ MARKET PRICE <span style='color: #ffffff; font-size: 30px; font-weight: 900; background: #000000; padding: 4px 12px; border-radius: 8px;'> {market_price:.2f} </span></div>
            <div style='color: #ffffff; font-size: 18px; font-weight: 700; margin-top: 12px; background: rgba(0,0,0,0.4); padding: 8px; border-radius: 8px;'>SL <span style='color: #ff9999; font-size: 20px;'>{stop_loss:.2f}</span> Niche | TP <span style='color: #ffff66; font-size: 20px;'>{take_profit:.2f}</span></div>
        </div>
        """, unsafe_allow_html=True)
    elif sell_percent >= 60:
        stop_loss = market_price + last_atr * 1.5
        take_profit = market_price - last_atr * 3.0
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #1a0000 0%, #800000 50%, #cc0000 100%); border: 3px solid #ff4444; padding: 22px; border-radius: 16px; text-align: center; box-shadow: 0 0 20px rgba(255,68,68,0.4);'>
            <div style='color: #ffffff; font-size: 28px; font-weight: 900; text-transform: uppercase; letter-spacing: 1.5px; text-shadow: 3px 3px 6px #000000;'>📉 SELL NOW</div>
            <div style='color: #ffe6e6; font-size: 20px; font-weight: 800; margin-top: 10px;'>@ MARKET PRICE <span style='color: #ffffff; font-size: 30px; font-weight: 900; background: #000000; padding: 4px 12px; border-radius: 8px;'> {market_price:.2f} </span></div>
            <div style='color: #ffffff; font-size: 18px; font-weight: 700; margin-top: 12px; background: rgba(0,0,0,0.4); padding: 8px; border-radius: 8px;'>SL <span style='color: #ff9999; font-size: 20px;'>{stop_loss:.2f}</span> Upar | TP <span style='color: #ffff66; font-size: 20px;'>{take_profit:.2f}</span></div>
        </div>
        """, unsafe_allow_html=True)
    else:
        stop_loss = market_price - last_atr
        take_profit = market_price + last_atr
        st.info(f"WAIT - BUY {buy_percent}% / SELL {sell_percent}% - Clear Signal Nahi Hai")

    st.write("")
    c1, c2, c3 = st.columns(3)
    c1.metric("BUY %", f"{buy_percent}%")
    c2.metric("SELL %", f"{sell_percent}%")
    c3.metric("MARKET PRICE", f"{market_price:.2f}")

    st.caption(f"✅ SPOT Data: Yahoo {yahoo_symbol} = {market_price:.2f} = TradingView {tradingview_symbol} SPOT - Future Nahi Hai")

    # Thesis - SL/TP nahi hai sirf reason
    with st.expander("📝 AI THESIS - Sirf Reason (SL/TP Nahi)"):
        for r in reasons:
            st.write(f"✔️ {r}")

    # ================= TRADINGVIEW SPOT CHART - LIVE COUNTDOWN =================
    st.markdown(f"### 📈 TradingView SPOT Chart - {tradingview_symbol} Live - 4467 Wala")
    tv_interval = TV_INTERVAL[selected_tf]
    # Advanced widget with countdown
    tv_url = f"https://s.tradingview.com/widgetembed/?frameElementId=tradingview_chart&symbol={tradingview_symbol}&interval={tv_interval}&hidesidetoolbar=0&symboledit=1&saveimage=1&toolbarbg=rgba(0,0,0,1)&studies=[]&theme=dark&style=1&timezone=Asia%2FKolkata&withdateranges=1&showpopupbutton=1"
    components.iframe(tv_url, height=700, scrolling=False)

    # ================= AI SL/TP CHART - SMOOTH =================
    st.markdown("### 🤖 AI SL/TP Chart - Smooth Pan/Zoom - TradingView Jaisa")
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=opens, high=highs, low=lows, close=closes, name="SPOT Price", increasing_line_color='#00ff88', decreasing_line_color='#ff4444'))
    fig.add_trace(go.Scatter(x=df.index, y=ema20, line=dict(color='#FFD700', width=1.8), name='EMA20'))
    fig.add_trace(go.Scatter(x=df.index, y=ema50, line=dict(color='#ffffff', width=1.2, dash='dot'), name='EMA50'))

    fig.add_hline(y=market_price, line_color="white", line_width=2, line_dash="dash", annotation_text=f"MARKET {market_price:.2f}", annotation_position="top right")
    fig.add_hline(y=stop_loss, line_color="#ff4444", line_width=2, line_dash="dash", annotation_text=f"SL {stop_loss:.2f}")
    fig.add_hline(y=take_profit, line_color="#00ff88", line_width=2, line_dash="dash", annotation_text=f"TP {take_profit:.2f}")

    fig.update_layout(
        template="plotly_dark",
        height=700,
        xaxis_rangeslider_visible=False,
        dragmode='pan',
        paper_bgcolor='black',
        plot_bgcolor='black',
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True, 'modeBarButtonsToAdd': ['drawline','drawrect','eraseshape'], 'modeBarButtonsToRemove': ['select2d','lasso2d']})
