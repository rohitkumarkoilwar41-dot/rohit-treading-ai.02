import streamlit as st, yfinance as yf, pandas as pd, plotly.graph_objects as go, requests, os
import numpy as np
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="Forex V2.0", layout="wide")
st.markdown("""
<style>
.main{background:#000}
div[data-testid="stMetric"]{background:#111; border:2px solid #FFD700; border-radius:14px; padding:10px}
div[data-testid="stMetricValue"]{color:#FFD700!important; font-weight:900}
.stButton>button{background:#FFD700; color:#000; font-weight:900; width:100%; height:65px; font-size:21px; border-radius:14px}
</style>
""", unsafe_allow_html=True)

st.title("🟨 JANTA AI - ALL CRYPTO + GOLD")

def save_data(pair, mp, sl, tp1, tp2, buy_score, sell_score):
    file = "trading_history.csv"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {"DateTime": [now],"Pair": [pair],"Market": [mp],"SL": [sl],"TP1": [tp1],"TP2": [tp2],"Buy%": [buy_score],"Sell%": [sell_score]}
    df_new = pd.DataFrame(data)
    if os.path.exists(file):
        try:
            df_old = pd.read_csv(file)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
        except:
            df_final = df_new
    else:
        df_final = df_new
    df_final.to_csv(file, index=False)
    return file

PAIRS = {
    "XAUUSD SPOT GOLD": ("XAUUSD=X", "OANDA:XAUUSD", 100),
    "XAGUSD SPOT SILVER": ("XAGUSD=X", "OANDA:XAGUSD", 100),
    "EURUSD": ("EURUSD=X", "OANDA:EURUSD", 10000),
    "GBPUSD": ("GBPUSD=X", "OANDA:GBPUSD", 10000),
    "USDJPY": ("USDJPY=X", "OANDA:USDJPY", 100),
    "AUDUSD": ("AUDUSD=X", "OANDA:AUDUSD", 10000),
    "BTC-USD": ("BTC-USD", "BINANCE:BTCUSDT", 1),
    "ETH-USD": ("ETH-USD", "BINANCE:ETHUSDT", 1),
    "SOL-USD": ("SOL-USD", "BINANCE:SOLUSDT", 1),
    "XRP-USD": ("XRP-USD", "BINANCE:XRPUSDT", 10000),
    "DOGE-USD": ("DOGE-USD", "BINANCE:DOGEUSDT", 100000),
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
        if "-USD" in pair_name and "XAU" not in pair_name and "XAG" not in pair_name and "EUR" not in pair_name and "GBP" not in pair_name and "USDJPY" not in pair_name and "AUDUSD" not in pair_name:
            symbol = pair_name.split("-")[0]
            binance_symbol = f"{symbol}USDT"
            if symbol=="SHIB": binance_symbol="1000SHIBUSDT"
            r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={binance_symbol}", timeout=5).json()
            price=float(r['price'])
            if symbol=="SHIB": price=price/1000
            return price
        if pair_name in PAIRS:
            t=PAIRS[pair_name][0]
            df=yf.download(t, period="1d", interval="1m", progress=False)
            if not df.empty: return float(df['Close'].iloc[-1])
    except: return None
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
                if t=="GC=F": df['Open']-=60; df['High']-=60; df['Low']-=60; df['Close']-=60
                if t=="SI=F": df['Open']-=1.5; df['High']-=1.5; df['Low']-=1.5; df['Close']-=1.5
                return df
        except: continue
    return pd.DataFrame()

col1,col2=st.columns(2)
with col1: pair=st.selectbox("Pair Select Karo - 18 Pairs", list(PAIRS.keys()), index=0)
with col2: tf=st.selectbox("Timeframe", ("1m","5m","15m","1h","4h","1d"), index=3)

y_sym, tv_sym, pt_mult = PAIRS[pair]

if st.button("START ANALYSIS"):
    live = get_live_price(pair)
    df = load_chart_fixed(y_sym, tf)
    if df.empty:
        st.error(f"{pair} ka chart load nahi hua, 10 sec baad dobara dabao"); st.stop()

    mp_yahoo = float(df['Close'].iloc[-1])
    mp = live if live and live>0 else mp_yahoo
    diff = mp - mp_yahoo
    df['Close']+=diff; df['High']+=diff; df['Low']+=diff; df['Open']+=diff

    c,h,l,o=df['Close'].astype(float),df['High'].astype(float),df['Low'].astype(float),df['Open'].astype(float)
    ema20=c.ewm(span=20, adjust=False).mean()
    ema50=c.ewm(span=50, adjust=False).mean()
    ema200=c.ewm(span=200, adjust=False).mean()
    tr=pd.concat([h-l,(h-c.shift(1)).abs(),(l-c.shift(1)).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    delta=c.diff()
    gain=delta.clip(lower=0).ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    loss=(-delta.clip(upper=0)).ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = np.where(loss < 1e-9, 100, gain/loss)
    rsi = pd.Series(100 - (100/(1+rs)), index=c.index).fillna(50)

    last=float(c.iloc[-1]); e20=float(ema20.iloc[-1]); e50=float(ema50.iloc[-1]); e200=float(ema200.iloc[-1])
    rsi_v=float(rsi.iloc[-1]); atr_v=float(atr.iloc[-1])
    if pd.isna(atr_v) or atr_v==0: atr_v = float((h.iloc[-14:].max() - l.iloc[-14:].min())/14)
    supp=float(l.iloc[-30:-1].min()); res=float(h.iloc[-30:-1].max())

    recent_high=h.iloc[-15:-2].max(); recent_low=l.iloc[-15:-2].min()
    choch_bull=last>recent_high; choch_bear=last<recent_low
    bos_bull=e20>e50>e200; bos_bear=e20<e50<e200

    prev_o=float(o.iloc[-2]); prev_c=float(c.iloc[-2]); last_o=float(o.iloc[-1])
    bull_eng=(prev_c<prev_o) and (last>last_o) and (last>prev_o) and (last_o<prev_c)
    bear_eng=(prev_c>prev_o) and (last<last_o) and (last<prev_o) and (last_o>prev_c)

    if tf == "1m" or tf == "5m": lookback_fvg = 100
    elif tf == "15m": lookback_fvg = 50
    elif tf == "1h": lookback_fvg = 24
    elif tf == "4h": lookback_fvg = 18
    else: lookback_fvg = 10

    # FINAL FIX: Chhota FVG + Fill wala FVG + LIVE ke andar wala FVG - Sab hat jayega
    bull_fvg=None; bear_fvg=None; bull_fvg_list=[]; bear_fvg_list=[]
    min_fvg_size = atr_v * 0.5
    for i in range(len(df)-lookback_fvg, len(df)-2):
        if i < 1: continue
        if h.iloc[i-1] < l.iloc[i+1] and (l.iloc[i+1] - h.iloc[i-1]) > min_fvg_size:
            fvg_low = float(h.iloc[i-1]); fvg_high = float(l.iloc[i+1])
            if abs(last - fvg_low) < atr_v*0.3 or abs(last - fvg_high) < atr_v*0.3: continue
            if fvg_low <= last <= fvg_high: continue
            mitigated=False
            for j in range(i+2, len(df)-1):
                if l.iloc[j] < fvg_high: mitigated=True; break
            if not mitigated:
                fv=(fvg_low, fvg_high); bull_fvg_list.append(fv); bull_fvg=fv
        if l.iloc[i-1] > h.iloc[i+1] and (l.iloc[i-1] - h.iloc[i+1]) > min_fvg_size:
            fvg_low = float(h.iloc[i+1]); fvg_high = float(l.iloc[i-1])
            if abs(last - fvg_low) < atr_v*0.3 or abs(last - fvg_high) < atr_v*0.3: continue
            if fvg_low <= last <= fvg_high: continue
            mitigated=False
            for j in range(i+2, len(df)-1):
                if h.iloc[j] > fvg_low: mitigated=True; break
            if not mitigated:
                fv=(fvg_low, fvg_high); bear_fvg_list.append(fv); bear_fvg=fv

    bull_ob=None; bear_ob=None
    for i in range(len(df)-15,len(df)-2):
        if c.iloc[i]<o.iloc[i] and c.iloc[i+1]>o.iloc[i+1] and c.iloc[i+2]>h.iloc[i]: bull_ob=(float(l.iloc[i]),float(h.iloc[i]))
        if c.iloc[i]>o.iloc[i] and c.iloc[i+1]<o.iloc[i+1] and c.iloc[i+2]<l.iloc[i]: bear_ob=(float(l.iloc[i]),float(h.iloc[i]))

    reasons=[]; score=50
    if last>e20>e50: score+=12; reasons.append(f"Bullish Trend - Price {last:.5f} > EMA20 {e20:.5f} > EMA50 {e50:.5f}")
    elif last<e20<e50: score-=12; reasons.append(f"Bearish Trend - Price {last:.5f} < EMA20 {e20:.5f} < EMA50 {e50:.5f}")
    if e20>e50>e200 and bos_bull: score+=10; reasons.append(f"BOS Bullish - EMA20>EMA50>EMA200 ({e200:.2f})")
    if e20<e50<e200 and bos_bear: score-=10; reasons.append(f"BOS Bearish - EMA20<EMA50<EMA200")
    if choch_bull: score+=12; reasons.append(f"CHoCH Bullish - Swing High Break {recent_high:.2f}")
    if choch_bear: score-=12; reasons.append(f"CHoCH Bearish - Swing Low Break {recent_low:.2f}")
    if bull_eng: score+=8; reasons.append("Bullish Engulfing Pattern - Strong Buy Signal")
    if bear_eng: score-=8; reasons.append("Bearish Engulfing Pattern - Strong Sell Signal")
    if bull_fvg: score+=10; reasons.append(f"Bullish FVG {bull_fvg[0]:.2f}-{bull_fvg[1]:.2f} ({lookback_fvg} candle me)")
    if bear_fvg: score-=10; reasons.append(f"Bearish FVG {bear_fvg[0]:.2f}-{bear_fvg[1]:.2f} ({lookback_fvg} candle me)")
    if bull_ob: score+=8; reasons.append(f"Bullish OB {bull_ob[0]:.2f}-{bull_ob[1]:.2f}")
    if bear_ob: score-=8; reasons.append(f"Bearish OB {bear_ob[0]:.2f}-{bear_ob[1]:.2f}")
    reasons.append(f"Support {supp:.5f} | Resistance {res:.5f} | ATR {atr_v:.5f}")
    reasons.append(f"LIVE {last:.5f} = {tv_sym} {last:.5f}")
    if 45<=rsi_v<=68: reasons.append(f"RSI Neutral {rsi_v:.1f}")
    elif rsi_v>70: reasons.append(f"RSI Overbought {rsi_v:.1f}")
    else: reasons.append(f"RSI Oversold {rsi_v:.1f}")

    buy_score=max(5,min(95,score)); sell_score=100-buy_score
    base_dist = max(mp*0.007, atr_v*2.8)
    def pts(d): return int(abs(d)*pt_mult)

    sl_plot=None; tp1_plot=None; tp2_plot=None
    if buy_score>=60:
        sl_short = mp - base_dist; sl_long = min(sl_short, supp - atr_v*0.5)
        tp_s1 = mp + base_dist*1.2; tp_s2 = mp + base_dist*2.0
        tp_l1 = mp + base_dist*2.0; tp_l2 = mp + base_dist*3.5; tp_l3 = mp + base_dist*5.5
        st.markdown(f"""<div style='background:linear-gradient(135deg,#002200,#00a336); border:3px solid #00ff88; padding:22px; border-radius:16px;'><div style='color:#fff; font-size:28px; font-weight:900; text-align:center;'>🚀 BUY {pair} @ {mp:.5f}</div><div style='display:flex; gap:10px; margin-top:14px;'><div style='flex:1; background:#000; border:2px solid #ffcc00; border-radius:12px; padding:12px; text-align:center;'><div style='color:#ffcc00; font-weight:900;'>⚡ SHORT</div><div style='color:#fff; font-size:12px; margin-top:6px;'>SL {sl_short:.5f} ({pts(mp-sl_short)} pt)<br>TP1 {tp_s1:.5f}<br>TP2 {tp_s2:.5f}</div></div><div style='flex:1; background:#000; border:2px solid #00ff88; border-radius:12px; padding:12px; text-align:center;'><div style='color:#00ff88; font-weight:900;'>🚀 LONG</div><div style='color:#fff; font-size:12px; margin-top:6px;'>SL {sl_long:.5f}<br>TP1 {tp_l1:.5f}<br>TP2 {tp_l2:.5f}<br>TP3 {tp_l3:.5f}</div></div></div></div>""", unsafe_allow_html=True)
        sl_plot,tp1_plot,tp2_plot = sl_long, tp_s1, tp_l2
    else:
        sl_short = mp + base_dist; sl_long = max(sl_short, res + atr_v*0.5)
        tp_s1 = mp - base_dist*1.2; tp_s2 = mp - base_dist*2.0
        tp_l1 = mp - base_dist*2.0; tp_l2 = mp - base_dist*3.5; tp_l3 = mp - base_dist*5.5
        st.markdown(f"""<div style='background:linear-gradient(135deg,#330000,#cc0000); border:3px solid #ff4444; padding:22px; border-radius:16px;'><div style='color:#fff; font-size:28px; font-weight:900; text-align:center;'>📉 SELL {pair} @ {mp:.5f}</div><div style='display:flex; gap:10px; margin-top:14px;'><div style='flex:1; background:#000; border:2px solid #ffcc00; border-radius:12px; padding:12px; text-align:center;'><div style='color:#ffcc00; font-weight:900;'>⚡ SHORT</div><div style='color:#fff; font-size:12px; margin-top:6px;'>SL {sl_short:.5f}<br>TP1 {tp_s1:.5f}<br>TP2 {tp_s2:.5f}</div></div><div style='flex:1; background:#000; border:2px solid #ff8888; border-radius:12px; padding:12px; text-align:center;'><div style='color:#ff8888; font-weight:900;'>📉 LONG</div><div style='color:#fff; font-size:12px; margin-top:6px;'>SL {sl_long:.5f}<br>TP1 {tp_l1:.5f}<br>TP2 {tp_l2:.5f}<br>TP3 {tp_l3:.5f}</div></div></div></div>""", unsafe_allow_html=True)
        sl_plot,tp1_plot,tp2_plot = sl_long, tp_s1, tp_l2

    saved_file = save_data(pair, mp, sl_plot, tp1_plot, tp2_plot, buy_score, sell_score)
    st.success(f"✅ Data Save Ho Gaya - {saved_file}")
    st.markdown("### 📁 Last 5 Saved")
    if os.path.exists("trading_history.csv"):
        st.dataframe(pd.read_csv("trading_history.csv").tail(5), use_container_width=True)

    c1,c2,c3=st.columns(3)
    c1.metric("BUY %", f"{buy_score}%"); c2.metric("SELL %", f"{sell_score}%"); c3.metric("LIVE", f"{mp:.5f}", delta=f"{diff:+.5f}")
    with st.expander("📝 AI THESIS - Reasons", expanded=True):
        for r in reasons: st.write(r)

    st.markdown(f"### 📈 TradingView {tv_sym} Live")
    components.iframe(f"https://s.tradingview.com/widgetembed/?symbol={tv_sym}&interval={TV_MAP[tf]}&theme=dark&style=1&timezone=Asia/Kolkata", height=550)

    fig=go.Figure(data=[go.Candlestick(x=df.index, open=o, high=h, low=l, close=c, name="Price")])
    fig.add_trace(go.Scatter(x=df.index, y=ema20, line=dict(color='#FFD700', width=1.5), name='EMA20'))
    fig.add_trace(go.Scatter(x=df.index, y=ema50, line=dict(color='#FF8C00', width=1.5), name='EMA50'))
    fig.add_hline(y=last,line_color="white",line_dash="dash",annotation_text=f"LIVE {last:.2f}")
    if sl_plot is not None:
        fig.add_hline(y=sl_plot, line_color="red", line_dash="dash", annotation_text=f"SL {sl_plot:.2f}")
        fig.add_hline(y=tp1_plot, line_color="green", line_dash="dot", annotation_text=f"TP1 {tp1_plot:.2f}")
        fig.add_hline(y=tp2_plot, line_color="green", line_dash="dot", annotation_text=f"TP2 {tp2_plot:.2f}")
    for fv in bull_fvg_list[-3:]: fig.add_hrect(y0=fv[0], y1=fv[1], fillcolor="green", opacity=0.18, line_width=0)
    for fv in bear_fvg_list[-3:]: fig.add_hrect(y0=fv[0], y1=fv[1], fillcolor="red", opacity=0.18, line_width=0)
    fig.update_layout(template="plotly_dark",height=600,xaxis_rangeslider_visible=False,dragmode='pan',paper_bgcolor='black',plot_bgcolor='black')
    st.plotly_chart(fig,use_container_width=True,config={'scrollZoom':True, 'displayModeBar':True})
