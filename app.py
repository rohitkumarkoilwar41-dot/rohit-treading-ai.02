import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import streamlit.components.v1 as components

st.set_page_config(page_title="Janta AI - SPOT", layout="wide")
st.markdown("<style>.main{background:#000}.stMetric{border:2px solid #FFD700; border-radius:12px; background:#111} div[data-testid='stMetricValue']{color:#FFD700!important}.stButton>button{background:#FFD700; color:#000; font-weight:900; width:100%; height:55px; font-size:18px; margin-top:15px}</style>", unsafe_allow_html=True)
st.title("🟨 JANTA AI - SPOT EXACT")

# YAHAN SPOT TICKER HAI - GC=F FUTURE HATA DIYA
PAIRS_YF = {
    "XAUUSD SPOT GOLD": "XAUUSD=X",
    "XAGUSD SPOT SILVER": "XAGUSD=X",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X",
    "BTC-USD": "BTC-USD",
    "ETH-USD": "ETH-USD",
    "SOL-USD": "SOL-USD"
}
PAIRS_TV = {
    "XAUUSD SPOT GOLD": "OANDA:XAUUSD",
    "XAGUSD SPOT SILVER": "OANDA:XAGUSD",
    "EURUSD": "OANDA:EURUSD",
    "GBPUSD": "OANDA:GBPUSD",
    "USDJPY": "OANDA:USDJPY",
    "AUDUSD": "OANDA:AUDUSD",
    "BTC-USD": "BINANCE:BTCUSD",
    "ETH-USD": "BINANCE:ETHUSD",
    "SOL-USD": "BINANCE:SOLUSD"
}
TV_MAP = {"1m":"1","5m":"5","15m":"15","1h":"60","4h":"240","1d":"D"}

DATA_FOLDER=Path("market_data_store"); DATA_FOLDER.mkdir(exist_ok=True)
def get_path(t,tf): return DATA_FOLDER / f"{t.replace('=','_')}_{tf}.csv"

@st.cache_data(ttl=60)
def load_data(ticker, tf):
    f=get_path(ticker,tf)
    old=pd.read_csv(f,index_col=0,parse_dates=True) if f.exists() else pd.DataFrame()
    try:
        # SPOT ke liye 60d me 1h tak data milta hai
        per="7d" if tf=="1m" else "60d"
        new=yf.download(ticker,period=per,interval=tf,auto_adjust=True,progress=False)
        if isinstance(new.columns,pd.MultiIndex): new.columns=new.columns.get_level_values(0)
    except: new=pd.DataFrame()
    if not new.empty:
        comb=pd.concat([old,new]); comb=comb[~comb.index.duplicated(keep='last')].sort_index().tail(500); comb.to_csv(f); return comb
    return old

c1,c2=st.columns(2)
with c1: pair_name=st.selectbox("Pair Select - Sab SPOT (9 pairs)", list(PAIRS_YF.keys()), index=0)
with c2: tf=st.selectbox("Timeframe", ("1m","5m","15m","1h","4h","1d"), index=3)

yf_sym=PAIRS_YF[pair_name]
tv_sym=PAIRS_TV[pair_name]

if st.button("START ANALYSIS"):
    df=load_data(yf_sym, tf)
    if df.empty or len(df)<20:
        st.error(f"{yf_sym} ka data Yahoo pe slow hai, 1 min ruk ke dobara dabao"); st.stop()

    closes,highs,lows,opens=df['Close'].astype(float),df['High'].astype(float),df['Low'].astype(float),df['Open'].astype(float)
    ema20=closes.ewm(20).mean()
    tr=pd.concat([highs-lows,(highs-closes.shift(1)).abs(),(lows-closes.shift(1)).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14).mean()

    market_price=float(closes.iloc[-1])
    atr_v=float(atr.iloc[-1])

    score=60 if market_price>float(ema20.iloc[-1]) else 40
    buy=score; sell=100-buy

    if buy>=60:
        sl=market_price - atr_v*1.5
        tp=market_price + atr_v*3
        st.success(f"🚀 BUY NOW @ MARKET {market_price:.2f} | SL {sl:.2f} Niche | TP {tp:.2f}")
    else:
        sl=market_price + atr_v*1.5
        tp=market_price - atr_v*3
        st.error(f"📉 SELL NOW @ MARKET {market_price:.2f} | SL {sl:.2f} Upar | TP {tp:.2f}")

    a,b,c=st.columns(3)
    a.metric("BUY %",f"{buy}%"); b.metric("SELL %",f"{sell}%"); c.metric("MARKET PRICE",f"{market_price:.2f}")
    st.caption(f"Yahoo SPOT {yf_sym} = {market_price:.2f} | TradingView {tv_sym} = Same ~4467 (1-2$ broker difference ho sakta hai)")

    with st.expander("📝 AI Reason"):
        st.write(f"✔️ Support: {float(lows.iloc[-20:-1].min()):.2f} | Resistance: {float(highs.iloc[-20:-1].max()):.2f}")
        st.write(f"✔️ EMA20: {float(ema20.iloc[-1]):.2f}")

    # TradingView - SPOT
    st.markdown("### 📈 TradingView SPOT Chart - Live 4467 wala")
    tv_url=f"https://s.tradingview.com/widgetembed/?symbol={tv_sym}&interval={TV_MAP[tf]}&theme=dark&style=1&timezone=Asia/Kolkata&withdateranges=1&hidesidetoolbar=0"
    components.iframe(tv_url, height=680, scrolling=False)

    # Smooth SL/TP Chart
    st.markdown("### 🤖 SL/TP Chart - Smooth")
    fig=go.Figure(data=[go.Candlestick(x=df.index, open=opens, high=highs, low=lows, close=closes, increasing_line_color='#FFD700', decreasing_line_color='#ff4444')])
    fig.add_trace(go.Scatter(x=df.index, y=ema20, line=dict(color='gold',width=1.5), name='EMA20'))
    fig.add_hline(y=market_price, line_color="white", line_width=2, line_dash="dash", annotation_text=f"MARKET {market_price:.2f}")
    fig.add_hline(y=sl, line_color="red", line_width=2, line_dash="dash", annotation_text=f"SL {sl:.2f}")
    fig.add_hline(y=tp, line_color="green", line_width=2, line_dash="dash", annotation_text=f"TP {tp:.2f}")
    fig.update_layout(template="plotly_dark", height=650, xaxis_rangeslider_visible=False, dragmode='pan', paper_bgcolor='black', plot_bgcolor='black')
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom':True,'displayModeBar':True})
