import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components
from tvDatafeed import TvDatafeed, Interval

st.set_page_config(layout="wide")
st.markdown("<style>.main{background:#000}.stMetric{border:2px solid #FFD700; border-radius:14px; background:#111}div[data-testid='stMetricValue']{color:#FFD700!important; font-weight:900}.stButton>button{background:#FFD700; color:#000; font-weight:900; width:100%; height:62px; font-size:20px; border-radius:12px}</style>", unsafe_allow_html=True)
st.title("🟨 JANTA AI - TRADINGVIEW SPOT")

# SIRF TRADINGVIEW SPOT - Yahoo nahi
PAIRS = {
    "XAUUSD SPOT GOLD": ("OANDA", "XAUUSD"),
    "XAGUSD SPOT SILVER": ("OANDA", "XAGUSD"),
    "EURUSD": ("OANDA", "EURUSD"),
    "GBPUSD": ("OANDA", "GBPUSD"),
    "USDJPY": ("OANDA", "USDJPY"),
    "BTC-USD": ("BINANCE", "BTCUSD"),
    "ETH-USD": ("BINANCE", "ETHUSD"),
    "SOL-USD": ("BINANCE", "SOLUSD"),
}

INTERVAL_MAP = {"1m": Interval.in_1_minute, "5m": Interval.in_5_minute, "15m": Interval.in_15_minute, "1h": Interval.in_1_hour, "4h": Interval.in_4_hour, "1d": Interval.in_daily}
TV_MAP = {"1m":"1","5m":"5","15m":"15","1h":"60","4h":"240","1d":"D"}

@st.cache_data(ttl=30)
def load_tv_data(exchange, symbol, tf):
    tv = TvDatafeed()
    df = tv.get_hist(symbol=symbol, exchange=exchange, interval=INTERVAL_MAP[tf], n_bars=500)
    return df

pair=st.selectbox("Pair - TRADINGVIEW SPOT (8 Pairs)", list(PAIRS.keys()), index=0)
tf=st.selectbox("Timeframe", ("1m","5m","15m","1h","4h","1d"), index=3)
exchange, tv_symbol = PAIRS[pair]

if st.button("START ANALYSIS"):
    with st.spinner(f"TradingView {exchange}:{tv_symbol} SPOT data le raha hu..."):
        df = load_tv_data(exchange, tv_symbol, tf)

    if df is None or df.empty or len(df)<20:
        st.error("TradingView thoda slow hai, 10 sec ruk ke dobara dabao")
        st.stop()

    closes,highs,lows,opens=df['close'].astype(float),df['high'].astype(float),df['low'].astype(float),df['open'].astype(float)
    ema20=closes.ewm(20).mean()
    atr=(highs-lows).ewm(alpha=1/14).mean()
    market_price=float(closes.iloc[-1]); atr_v=float(atr.iloc[-1])

    buy=65 if market_price>float(ema20.iloc[-1]) else 35
    sell=100-buy

    if buy>=60:
        sl=market_price - atr_v*1.5; tp=market_price + atr_v*3
        st.markdown(f"<div style='background:linear-gradient(135deg,#001a00,#00a336); border:3px solid #00ff88; padding:22px; border-radius:16px; text-align:center;'><div style='color:#fff; font-size:28px; font-weight:900; text-shadow:2px 2px 4px #000;'>🚀 BUY NOW</div><div style='color:#fff; font-size:22px; font-weight:800; margin-top:10px;'>@ MARKET <span style='background:#000; padding:4px 12px; border-radius:8px; font-size:30px;'>{market_price:.2f}</span></div><div style='color:#fff; font-size:18px; font-weight:700; margin-top:12px;'>SL {sl:.2f} Niche | TP {tp:.2f}</div></div>", unsafe_allow_html=True)
    else:
        sl=market_price + atr_v*1.5; tp=market_price - atr_v*3
        st.markdown(f"<div style='background:linear-gradient(135deg,#1a0000,#cc0000); border:3px solid #ff4444; padding:22px; border-radius:16px; text-align:center;'><div style='color:#fff; font-size:28px; font-weight:900; text-shadow:2px 2px 4px #000;'>📉 SELL NOW</div><div style='color:#fff; font-size:22px; font-weight:800; margin-top:10px;'>@ MARKET <span style='background:#000; padding:4px 12px; border-radius:8px; font-size:30px;'>{market_price:.2f}</span></div><div style='color:#fff; font-size:18px; font-weight:700; margin-top:12px;'>SL {sl:.2f} Upar | TP {tp:.2f}</div></div>", unsafe_allow_html=True)

    m1,m2,m3=st.columns(3)
    m1.metric("BUY %",f"{buy}%"); m2.metric("SELL %",f"{sell}%"); m3.metric("MARKET PRICE",f"{market_price:.2f}")
    st.caption(f"✅ TradingView {exchange}:{tv_symbol} = {market_price:.2f} - Bilkul SPOT, Future Nahi")

    st.markdown(f"### 📈 TradingView SPOT Chart - {exchange}:{tv_symbol} Live")
    components.iframe(f"https://s.tradingview.com/widgetembed/?symbol={exchange}:{tv_symbol}&interval={TV_MAP[tf]}&theme=dark&style=1&timezone=Asia/Kolkata&withdateranges=1", height=700)

    st.markdown("### 🤖 AI SL/TP Chart")
    fig=go.Figure(data=[go.Candlestick(x=df.index, open=opens, high=highs, low=lows, close=closes)])
    fig.add_hline(y=market_price, line_color="white", annotation_text=f"MARKET {market_price:.2f}")
    fig.add_hline(y=sl, line_color="red", annotation_text=f"SL {sl:.2f}")
    fig.add_hline(y=tp, line_color="green", annotation_text=f"TP {tp:.2f}")
    fig.update_layout(template="plotly_dark", height=650, xaxis_rangeslider_visible=False, dragmode='pan', paper_bgcolor='black')
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom':True})
