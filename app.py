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

st.title("🟨 JANTA AI - ALL CRYPTO + GOLD")

# ========= SABHI PAIRS - Crypto wapas =========
PAIRS = {
    # GOLD SILVER
    "XAUUSD SPOT GOLD": ("XAUUSD=X", "OANDA:XAUUSD", 100),
    "XAGUSD SPOT SILVER": ("XAGUSD=X", "OANDA:XAGUSD", 100),
    # FOREX
    "EURUSD": ("EURUSD=X", "OANDA:EURUSD", 10000),
    "GBPUSD": ("GBPUSD=X", "OANDA:GBPUSD", 10000),
    "USDJPY": ("USDJPY=X", "OANDA:USDJPY", 100),
    "AUDUSD": ("AUDUSD=X", "OANDA:AUDUSD", 10000),
    # CRYPTO - Sab wapas
    "BTC-USD": ("BTC-USD", "BINANCE:BTCUSDT", 1),
    "ETH-USD": ("ETH-USD", "BINANCE:ETHUSDT", 1),
    "SOL-USD": ("SOL-USD", "BINANCE:SOLUSDT", 1),
    "XRP-USD": ("XRP-USD", "BINANCE:XRPUSDT", 10000),
    "DOGE-USD": ("DOGE-USD", "BINANCE:DOGEUSDT", 100000),
    "BNB-USD": ("BNB-USD", "BINANCE:BNBUSDT", 1),
    "ADA-USD": ("ADA-USD", "BINANCE:ADAUSDT", 10000),
    "AVAX-USD": ("AVAX-USD", "BINANCE:AVAXUSDT", 1),
    "SHIB-USD": ("SHIB-USD", "BINANCE:SHIBUSDT", 10000000),
    "DOT-USD": ("DOT-USD", "BINANCE:DOTUSDT", 1000),
    "LINK-USD": ("LINK-USD", "BINANCE:LINKUSDT", 100),
    "MATIC-USD": ("MATIC-USD", "BINANCE:MATICUSDT", 10000),
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

        # Crypto ka LIVE - Binance se - Sab ke liye
        if "-USD" in pair_name and "XAU" not in pair_name and "XAG" not in pair_name and "EUR" not in pair_name and "GBP" not in pair_name and "USDJPY" not in pair_name and "AUDUSD" not in pair_name:
            symbol = pair_name.split("-")[0] # BTC-USD -> BTC
            binance_symbol = f"{symbol}USDT"
            # SHIB ke liye 1000SHIBUSDT hota hai
            if symbol=="SHIB":
                binance_symbol="1000SHIBUSDT"
                r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={binance_symbol}", timeout=5).json()
                return float(r['price'])/1000
            r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={binance_symbol}", timeout=5).json()
            return float(r['price'])

        # Forex
        if pair_name in PAIRS:
            t=PAIRS[pair_name][0]
            df=yf.download(t, period="1d", interval="1m", progress=False)
            if not df.empty:
                return float(df['Close'].iloc[-1])
    except:
        return None
    return None

@st.cache_data(ttl=40)
def load_chart_fixed(ticker, tf):
    tickers_to_try = [ticker]
    if "XAUUSD" in ticker: tickers_to_try = ["XAUUSD=X", "GC=F"]
    if "XAGUSD" in ticker: tickers_to_try = ["XAGUSD=X", "SI=F"]

    for t in tickers_to_try:
        try:
            period = "10d" if tf in ["1m","5m","15m","1h"] else "60d"
            df=yf.download(t, period=period, interval=tf, auto_adjust=True, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns=df.columns.get_level_values(0)
            if df is not None and not df.empty and len(df)>20:
                if t=="GC=F":
                    df['Open']-=60; df['High']-=60; df['Low']-=60; df['Close']-=60
                if t=="SI=F":
                    df['Open']-=1.5; df['High']-=1.5; df['Low']-=1.5; df['Close']-=1.5
                return df
        except:
            continue
    return pd.DataFrame()

col1,col2=st.columns(2)
with col1:
    pair=st.selectbox("Pair Select Karo - 18 Pairs", list(PAIRS.keys()), index=0)
with col2:
    tf=st.selectbox("Timeframe", ("1m","5m","15m","1h","4h","1d"), index=3)

y_sym, tv_sym, pt_mult = PAIRS[pair]

if st.button("START ANALYSIS"):
    live = get_live_price(pair)
    df = load_chart_fixed(y_sym, tf)

    if df.empty:
        st.error(f"{pair} ka chart load nahi hua")
        st.stop()

    mp_yahoo = float(df['Close'].iloc[-1])
    mp = live if live and live>0 else mp_yahoo
    diff = mp - mp_yahoo
    df['Close']+=diff; df['High']+=diff; df['Low']+=diff; df['Open']+=diff

    closes,highs,lows,opens=df['Close'].astype(float),df['High'].astype(float),df['Low'].astype(float),df['Open'].astype(float)
    ema20=closes.ewm(span=20).mean(); ema50=closes.ewm(span=50).mean()
    tr=pd.concat([highs-lows,(highs-closes.shift(1)).abs(),(lows-closes.shift(1)).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14).mean()
    atr_v=float(atr.iloc[-1]); ema20_v=float(ema20.iloc[-1]); ema50_v=float(ema50.iloc[-1])

    delta=closes.diff(); gain=(delta.where(delta>0,0)).ewm(alpha=1/14).mean(); loss=(-delta.where(delta<0,0)).ewm(alpha=1/14).mean()
    rs=gain/loss; rsi=100-(100/(1+rs)); rsi_v=float(rsi.iloc[-1])

    support=float(lows.iloc[-30:-1].min()); resistance=float(highs.iloc[-30:-1].max())

    reasons=[]
    score=50
    if mp > ema20_v > ema50_v:
        score+=15
        reasons.append(f"✅ Bullish Trend - Price {mp:.5f} > EMA20 {ema20_v:.5f} > EMA50 {ema50_v:.5f}")
    elif mp < ema20_v < ema50_v:
        score-=15
        reasons.append(f"❌ Bearish Trend - Price {mp:.5f} < EMA20 {ema20_v:.5f} < EMA50 {ema50_v:.5f}")
    else:
        reasons.append(f"⚠️ Sideways - Price {mp:.5f} EMA ke aas paas")

    if rsi_v > 70: reasons.append(f"⚠️ RSI Overbought {rsi_v:.1f}"); score-=5
    elif rsi_v < 30: reasons.append(f"⚠️ RSI Oversold {rsi_v:.1f}"); score+=5
    else: reasons.append(f"✅ RSI Neutral {rsi_v:.1f}")

    reasons.append(f"📊 Support {support:.5f} | Resistance {resistance:.5f} | ATR {atr_v:.5f}")
    reasons.append(f"🔴 LIVE {mp:.5f} = {tv_sym} {mp:.5f}")

    buy_score=max(5,min(95,score)); sell_score=100-buy_score
    base_dist = max(mp*0.007, atr_v*2.8)
    def pts(d): return int(abs(d)*pt_mult)

    if buy_score>=60:
        sl_short = mp - base_dist; sl_long = min(sl_short, support - atr_v*0.5)
        tp_s1 = mp + base_dist*1.2; tp_s2 = mp + base_dist*2.0
        tp_l1 = mp + base_dist*2.0; tp_l2 = mp + base_dist*3.5; tp_l3 = mp + base_dist*5.5
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#002200,#00a336); border:3px solid #00ff88; padding:22px; border-radius:16px;'>
            <div style='color:#fff; font-size:28px; font-weight:900; text-align:center;'>🚀 BUY {pair} @ {mp:.5f}</div>
            <div style='display:flex; gap:10px; margin-top:14px;'>
                <div style='flex:1; background:#000; border:2px solid #ffcc00; border-radius:12px; padding:12px; text-align:center;'>
                    <div style='color:#ffcc00; font-weight:900;'>⚡ SHORT</div>
                    <div style='color:#fff; font-size:12px; margin-top:6px;'>SL {sl_short:.5f} ({pts(mp-sl_short)} pt)<br>TP1 {tp_s1:.5f}<br>TP2 {tp_s2:.5f}</div>
                </div>
                <div style='flex:1; background:#000; border:2px solid #00ff88; border-radius:12px; padding:12px; text-align:center;'>
                    <div style='color:#00ff88; font-weight:900;'>🚀 LONG</div>
                    <div style='color:#fff; font-size:12px; margin-top:6px;'>SL {sl_long:.5f}<br>TP1 {tp_l1:.5f}<br>TP2 {tp_l2:.5f}<br>TP3 {tp_l3:.5f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        sl_plot,tp1_plot,tp2_plot,tp3_plot = sl_long, tp_s1, tp_l2, tp_l3
    else:
        sl_short = mp + base_dist; sl_long = max(sl_short, resistance + atr_v*0.5)
        tp_s1 = mp - base_dist*1.2; tp_s2 = mp - base_dist*2.0
        tp_l1 = mp - base_dist*2.0; tp_l2 = mp - base_dist*3.5; tp_l3 = mp - base_dist*5.5
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#330000,#cc0000); border:3px solid #ff4444; padding:22px; border-radius:16px;'>
            <div style='color:#fff; font-size:28px; font-weight:900; text-align:center;'>📉 SELL {pair} @ {mp:.5f}</div>
            <div style='display:flex; gap:10px; margin-top:14px;'>
                <div style='flex:1; background:#000; border:2px solid #ffcc00; border-radius:12px; padding:12px; text-align:center;'>
                    <div style='color:#ffcc00; font-weight:900;'>⚡ SHORT</div>
                    <div style='color:#fff; font-size:12px; margin-top:6px;'>SL {sl_short:.5f}<br>TP1 {tp_s1:.5f}<br>TP2 {tp_s2:.5f}</div>
                </div>
                <div style='flex:1; background:#000; border:2px solid #ff8888; border-radius:12px; padding:12px; text-align:center;'>
                    <div style='color:#ff8888; font-weight:900;'>📉 LONG</div>
                    <div style='color:#fff; font-size:12px; margin-top:6px;'>SL {sl_long:.5f}<br>TP1 {tp_l1:.5f}<br>TP2 {tp_l2:.5f}<br>TP3 {tp_l3:.5f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        sl_plot,tp1_plot,tp2_plot,tp3_plot = sl_long, tp_s1, tp_l2, tp_l3

    c1,c2,c3=st.columns(3)
    c1.metric("BUY %", f"{buy_score}%"); c2.metric("SELL %", f"{sell_score}%"); c3.metric("LIVE", f"{mp:.5f}", delta=f"{diff:+.5f}")

    with st.expander("📝 AI THESIS - Reasons", expanded=True):
        for r in reasons: st.write(r)

    st.markdown(f"### 📈 TradingView {tv_sym} Live")
    components.iframe(f"https://s.tradingview.com/widgetembed/?symbol={tv_sym}&interval={TV_MAP[tf]}&theme=dark&style=1&timezone=Asia/Kolkata&withdateranges=1", height=720)

    fig=go.Figure(data=[go.Candlestick(x=df.index, open=opens, high=highs, low=lows, close=closes, increasing_line_color='#00ff88', decreasing_line_color='#ff4444')])
    fig.add_trace(go.Scatter(x=df.index, y=ema20, line=dict(color='#FFD700', width=2), name='EMA20'))
    fig.add_hline(y=mp, line_color="white", line_width=2, annotation_text=f"LIVE {mp:.5f}")
    fig.add_hline(y=sl_plot, line_color="red", line_width=2, line_dash="dash", annotation_text=f"SL {sl_plot:.5f}")
    fig.add_hline(y=tp1_plot, line_color="green", line_width=2, annotation_text=f"TP1 {tp1_plot:.5f}")
    fig.update_layout(template="plotly_dark", height=750, xaxis_rangeslider_visible=False, dragmode='pan', paper_bgcolor='black', plot_bgcolor='black')
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom':True})
