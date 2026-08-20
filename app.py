import streamlit as st, yfinance as yf, pandas as pd, plotly.graph_objects as go, requests
import streamlit.components.v1 as components

st.set_page_config(page_title="Janta AI - Final", layout="wide")
st.markdown("""
<style>
.main{background:#000}
div[data-testid="stMetric"]{background:#111; border:2px solid #FFD700; border-radius:14px; padding:10px}
div[data-testid="stMetricValue"]{color:#FFD700!important; font-weight:900}
.stButton>button{background:#FFD700; color:#000; font-weight:900; width:100%; height:65px; font-size:21px; border-radius:14px}
</style>
""", unsafe_allow_html=True)

st.title("🟨 JANTA AI - FINAL LIVE")

PAIRS = {
    "XAUUSD SPOT GOLD": ("XAUUSD=X", "OANDA:XAUUSD", 100),
    "XAGUSD SPOT SILVER": ("XAGUSD=X", "OANDA:XAGUSD", 100),
    "EURUSD": ("EURUSD=X", "OANDA:EURUSD", 10000),
    "GBPUSD": ("GBPUSD=X", "OANDA:GBPUSD", 10000),
    "USDJPY": ("USDJPY=X", "OANDA:USDJPY", 100),
    "AUDUSD": ("AUDUSD=X", "OANDA:AUDUSD", 10000),
    "BTC-USD": ("BTC-USD", "BINANCE:BTCUSD", 1),
    "ETH-USD": ("ETH-USD", "BINANCE:ETHUSD", 1),
    "SOL-USD": ("SOL-USD", "BINANCE:SOLUSD", 1),
}
TV_MAP={"1m":"1","5m":"5","15m":"15","1h":"60","4h":"240","1d":"D"}

def get_live_price(pair_name):
    try:
        if "XAUUSD" in pair_name:
            r=requests.get("https://api.gold-api.com/price/XAU", timeout=5).json()
            return float(r['price'])
        if "XAGUSD" in pair_name:
            r=requests.get("https://api.gold-api.com/price/XAG", timeout=5).json()
            return float(r['price'])
        if "BTC" in pair_name:
            r=requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5).json()
            return float(r['price'])
        if "ETH" in pair_name:
            r=requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT", timeout=5).json()
            return float(r['price'])
        if "SOL" in pair_name:
            r=requests.get("https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT", timeout=5).json()
            return float(r['price'])
        # Forex ke liye 1m ka latest Yahoo hi live jaisa hai
        if pair_name in PAIRS:
            t=PAIRS[pair_name][0]
            df=yf.download(t, period="1d", interval="1m", progress=False)
            if not df.empty:
                return float(df['Close'].iloc[-1])
    except:
        return None
    return None

@st.cache_data(ttl=40)
def load_chart(ticker, tf):
    df=yf.download(ticker, period="10d", interval=tf, auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex): df.columns=df.columns.get_level_values(0)
    return df

col1,col2=st.columns(2)
with col1:
    pair=st.selectbox("Pair Select Karo", list(PAIRS.keys()), index=0)
with col2:
    tf=st.selectbox("Timeframe", ("1m","5m","15m","1h","4h","1d"), index=3)

y_sym, tv_sym, pt_mult = PAIRS[pair]

if st.button("START ANALYSIS"):
    live = get_live_price(pair)
    df = load_chart(y_sym, tf)

    if df.empty:
        st.error("Chart load nahi hua, dobara dabao")
        st.stop()

    mp_yahoo = float(df['Close'].iloc[-1])
    mp = live if live and live>0 else mp_yahoo

    # Chart ko live price pe shift
    diff = mp - mp_yahoo
    df['Close']+=diff; df['High']+=diff; df['Low']+=diff; df['Open']+=diff

    closes,highs,lows,opens=df['Close'].astype(float),df['High'].astype(float),df['Low'].astype(float),df['Open'].astype(float)
    ema20=closes.ewm(20).mean(); ema50=closes.ewm(50).mean()
    tr=pd.concat([highs-lows,(highs-closes.shift(1)).abs(),(lows-closes.shift(1)).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14).mean()
    atr_v=float(atr.iloc[-1])

    buy_score=65 if mp>float(ema20.iloc[-1]) else 35
    sell_score=100-buy_score

    # SL TP Calculation - Point me
    base_dist = max(mp*0.007, atr_v*2.8) # 0.7% min
    def pts(d): return int(abs(d)*pt_mult)

    swing_high=float(highs.iloc[-30:-1].max())
    swing_low=float(lows.iloc[-30:-1].min())

    if buy_score>=60:
        sl_short = mp - base_dist
        sl_long = min(sl_short, swing_low - atr_v*0.5)
        tp_s1 = mp + base_dist*1.2
        tp_s2 = mp + base_dist*2.0
        tp_l1 = mp + base_dist*2.0
        tp_l2 = mp + base_dist*3.5
        tp_l3 = mp + base_dist*5.5

        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#002200,#00a336); border:3px solid #00ff88; padding:22px; border-radius:16px;'>
            <div style='color:#00ff88; font-size:13px; text-align:center;'>🔴 LIVE PRICE {mp:.2f} - Yahoo {mp_yahoo:.2f} se {diff:.2f} tez</div>
            <div style='color:#fff; font-size:30px; font-weight:900; text-align:center; margin-top:6px;'>🚀 BUY NOW @ {mp:.2f}</div>
            <div style='display:flex; gap:10px; margin-top:14px;'>
                <div style='flex:1; background:#000; border:2px solid #ffcc00; border-radius:12px; padding:12px; text-align:center;'>
                    <div style='color:#ffcc00; font-weight:900;'>⚡ SHORT (Scalp)</div>
                    <div style='color:#fff; font-size:13px; margin-top:6px;'>SL {sl_short:.2f} ({pts(mp-sl_short)} pt)<br>TP1 {tp_s1:.2f} ({pts(tp_s1-mp)} pt)<br>TP2 {tp_s2:.2f} ({pts(tp_s2-mp)} pt)</div>
                </div>
                <div style='flex:1; background:#000; border:2px solid #00ff88; border-radius:12px; padding:12px; text-align:center;'>
                    <div style='color:#00ff88; font-weight:900;'>🚀 LONG (Swing)</div>
                    <div style='color:#fff; font-size:13px; margin-top:6px;'>SL {sl_long:.2f} ({pts(mp-sl_long)} pt)<br>TP1 {tp_l1:.2f}<br>TP2 {tp_l2:.2f}<br>TP3 {tp_l3:.2f} ({pts(tp_l3-mp)} pt)</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        sl_plot,tp1_plot,tp2_plot,tp3_plot = sl_long, tp_s1, tp_l2, tp_l3

    else:
        sl_short = mp + base_dist
        sl_long = max(sl_short, swing_high + atr_v*0.5)
        tp_s1 = mp - base_dist*1.2
        tp_s2 = mp - base_dist*2.0
        tp_l1 = mp - base_dist*2.0
        tp_l2 = mp - base_dist*3.5
        tp_l3 = mp - base_dist*5.5

        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#330000,#cc0000); border:3px solid #ff4444; padding:22px; border-radius:16px;'>
            <div style='color:#ff8888; font-size:13px; text-align:center;'>🔴 LIVE PRICE {mp:.2f} - Yahoo {mp_yahoo:.2f} se {diff:.2f} tez</div>
            <div style='color:#fff; font-size:30px; font-weight:900; text-align:center; margin-top:6px;'>📉 SELL NOW @ {mp:.2f}</div>
            <div style='display:flex; gap:10px; margin-top:14px;'>
                <div style='flex:1; background:#000; border:2px solid #ffcc00; border-radius:12px; padding:12px; text-align:center;'>
                    <div style='color:#ffcc00; font-weight:900;'>⚡ SHORT (Scalp)</div>
                    <div style='color:#fff; font-size:13px; margin-top:6px;'>SL {sl_short:.2f} ({pts(sl_short-mp)} pt)<br>TP1 {tp_s1:.2f} ({pts(mp-tp_s1)} pt)<br>TP2 {tp_s2:.2f} ({pts(mp-tp_s2)} pt)</div>
                </div>
                <div style='flex:1; background:#000; border:2px solid #ff8888; border-radius:12px; padding:12px; text-align:center;'>
                    <div style='color:#ff8888; font-weight:900;'>📉 LONG (Swing)</div>
                    <div style='color:#fff; font-size:13px; margin-top:6px;'>SL {sl_long:.2f} ({pts(sl_long-mp)} pt)<br>TP1 {tp_l1:.2f}<br>TP2 {tp_l2:.2f}<br>TP3 {tp_l3:.2f} ({pts(mp-tp_l3)} pt)</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        sl_plot,tp1_plot,tp2_plot,tp3_plot = sl_long, tp_s1, tp_l2, tp_l3

    c1,c2,c3=st.columns(3)
    c1.metric("BUY %", f"{buy_score}%")
    c2.metric("SELL %", f"{sell_score}%")
    c3.metric("LIVE MARKET", f"{mp:.2f}", delta=f"{diff:.2f}")

    st.caption(f"✅ {pair} LIVE {mp:.2f} = {tv_sym} {mp:.2f} | Point: 0.01 lot pe {pts(base_dist)} pt ka SL")

    st.markdown(f"### 📈 TradingView {tv_sym} Live Chart - {mp:.2f}")
    components.iframe(f"https://s.tradingview.com/widgetembed/?symbol={tv_sym}&interval={TV_MAP[tf]}&theme=dark&style=1&timezone=Asia/Kolkata&withdateranges=1", height=720)

    fig=go.Figure(data=[go.Candlestick(x=df.index, open=opens, high=highs, low=lows, close=closes, increasing_line_color='#00ff88', decreasing_line_color='#ff4444')])
    fig.add_hline(y=mp, line_color="white", line_width=2, annotation_text=f"LIVE MARKET {mp:.2f}")
    fig.add_hline(y=sl_plot, line_color="red", line_width=2, line_dash="dash", annotation_text=f"SL {sl_plot:.2f} ({pts(sl_plot-mp)}pt)")
    fig.add_hline(y=tp1_plot, line_color="#00ff88", line_width=2, annotation_text=f"TP1 {tp1_plot:.2f}")
    fig.add_hline(y=tp2_plot, line_color="#FFD700", line_dash="dot", annotation_text=f"TP2 {tp2_plot:.2f}")
    fig.add_hline(y=tp3_plot, line_color="#00ccff", line_dash="dot", annotation_text=f"TP3 {tp3_plot:.2f}")
    fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False, dragmode='pan', paper_bgcolor='black', plot_bgcolor='black')
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom':True})
