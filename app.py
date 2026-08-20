import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import streamlit.components.v1 as components

st.set_page_config(page_title="Janta AI - Final", layout="wide")
st.markdown("<style>.main{background-color:#000}.stMetric{border:2px solid #FFD700; border-radius:12px; background:#111} div[data-testid='stMetricValue']{color:#FFD700!important}.stButton>button{background:#FFD700; color:#000; font-weight:900; width:100%; height:55px; font-size:18px}</style>", unsafe_allow_html=True)
st.title("🟨 JANTA AI - FINAL")

PAIRS_YF = {"XAUUSD SPOT GOLD - Main": "GC=F", "XAGUSD SPOT SILVER": "SI=F", "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "BTC-USD": "BTC-USD"}
PAIRS_TV = {"XAUUSD SPOT GOLD - Main": "OANDA:XAUUSD", "XAGUSD SPOT SILVER": "OANDA:XAGUSD", "EURUSD": "OANDA:EURUSD", "GBPUSD": "OANDA:GBPUSD", "BTC-USD": "BINANCE:BTCUSD"}
TV_MAP = {"1m":"1","5m":"5","15m":"15","1h":"60","4h":"240","1d":"D"}

DATA_FOLDER = Path("market_data_store"); DATA_FOLDER.mkdir(exist_ok=True)
def get_path(t, tf): return DATA_FOLDER / f"{t}_{tf}.csv"

@st.cache_data(ttl=300)
def load_data(ticker, tf):
    f=get_path(ticker,tf)
    old=pd.read_csv(f,index_col=0,parse_dates=True) if f.exists() else pd.DataFrame()
    try:
        per="7d" if tf=="1m" else "60d" if tf in ["5m","15m","1h"] else "1y"
        new=yf.download(ticker,period=per,interval=tf,auto_adjust=True,progress=False)
        if isinstance(new.columns,pd.MultiIndex): new.columns=new.columns.get_level_values(0)
    except: new=pd.DataFrame()
    if not new.empty:
        comb=pd.concat([old,new]); comb=comb[~comb.index.duplicated(keep='last')].sort_index().tail(500); comb.to_csv(f); return comb
    return old

c1,c2=st.columns(2)
with c1: pair_name=st.selectbox("Pair Select - Sab SPOT", list(PAIRS_YF.keys()), index=0)
with c2: tf=st.selectbox("Timeframe", ("1m","5m","15m","1h","4h","1d"), index=3)

if st.button("START ANALYSIS"):
    df=load_data(PAIRS_YF[pair_name], tf)
    if df.empty or len(df)<30: st.error("Data slow, dobara dabao"); st.stop()

    closes,highs,lows,opens=df['Close'].astype(float),df['High'].astype(float),df['Low'].astype(float),df['Open'].astype(float)
    ema20,ema50=closes.ewm(20).mean(),closes.ewm(50).mean()
    tr=pd.concat([highs-lows,(highs-closes.shift(1)).abs(),(lows-closes.shift(1)).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14).mean()

    last=float(closes.iloc[-1]); atr_v=float(atr.iloc[-1]); e20=float(ema20.iloc[-1])
    support=float(lows.iloc[-20:-1].min()); resistance=float(highs.iloc[-20:-1].max())

    score=50
    if last>e20: score+=15
    else: score-=15
    buy=max(5,min(95,score)); sell=100-buy
    market_price=last

    # MARKET PRICE SE HI BUY/SELL - ENTRY SHABD HATA DIYA
    if buy>=60:
        sl=market_price - atr_v*1.2
        tp=market_price + atr_v*2.5
        st.success(f"🚀 BUY NOW @ MARKET {market_price:.2f} | SL {sl:.2f} Niche | TP {tp:.2f}")
    elif sell>=60:
        sl=market_price + atr_v*1.2
        tp=market_price - atr_v*2.5
        st.error(f"📉 SELL NOW @ MARKET {market_price:.2f} | SL {sl:.2f} Upar | TP {tp:.2f}")
    else:
        sl,tp=market_price-atr_v,market_price+atr_v
        st.info(f"WAIT - BUY {buy}% / SELL {sell}%")

    m1,m2,m3=st.columns(3)
    m1.metric("BUY %",f"{buy}%"); m2.metric("SELL %",f"{sell}%"); m3.metric("MARKET PRICE",f"{market_price:.2f}")

    with st.expander("📝 AI THESIS - Sirf Reason, SL/TP nahi"):
        st.write(f"✔️ Support: {support:.2f} | Resistance: {resistance:.2f}")
        st.write(f"✔️ EMA20: {e20:.2f} | Price: {last:.2f}")
        st.write(f"✔️ ATR: {atr_v:.2f}")

    # TradingView SPOT - Live Countdown wala
    st.markdown("### 📈 TradingView SPOT Chart - Live Countdown")
    tv_sym=PAIRS_TV[pair_name]
    tv_url=f"https://s.tradingview.com/widgetembed/?symbol={tv_sym}&interval={TV_MAP[tf]}&theme=dark&style=1&timezone=Asia/Kolkata&withdateranges=1&hidesidetoolbar=0&studies=Volume@tv-basicstudies"
    components.iframe(tv_url, height=650, scrolling=False)

    # SL/TP Chart - Smooth, TradingView jaisa
    st.markdown("### 🤖 SL/TP Chart - Smooth Pan & Zoom")
    fig=go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=opens, high=highs, low=lows, close=closes, name="Price", increasing_line_color='#FFD700', decreasing_line_color='#ff4444'))
    fig.add_trace(go.Scatter(x=df.index, y=ema20, line=dict(color='gold',width=1.5), name='EMA20'))
    fig.add_hline(y=market_price, line_color="white", line_width=2, line_dash="dash", annotation_text=f"MARKET {market_price:.2f}")
    fig.add_hline(y=sl, line_color="red", line_width=2, line_dash="dash", annotation_text=f"SL {sl:.2f}")
    fig.add_hline(y=tp, line_color="green", line_width=2, line_dash="dash", annotation_text=f"TP {tp:.2f}")
    fig.update_layout(template="plotly_dark", height=650, xaxis_rangeslider_visible=False, dragmode='pan', paper_bgcolor='black', plot_bgcolor='black', margin=dict(l=10,r=10,t=30,b=10))
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom':True,'displayModeBar':True,'modeBarButtonsToRemove':['select2d','lasso2d']})
