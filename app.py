import streamlit as st, yfinance as yf, pandas as pd, plotly.graph_objects as go, requests, os
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="Janta AI - Final FVG", layout="wide")
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
            r = requests.get("https://gold-api.com", timeout=5).json()
            return float(r['price'])
        if "XAGUSD" in pair_name:
            r = requests.get("https://gold-api.com", timeout=5).json()
            return float(r['price'])
        if "-USD" in pair_name and "XAU" not in pair_name and "XAG" not in pair_name:
            symbol = pair_name.split("-")[0]
            binance_symbol = f"{symbol}USDT"
            if symbol == "SHIB": binance_symbol = "1000SHIBUSDT"
            r = requests.get(f"https://binance.com{binance_symbol}", timeout=5).json()
            price = float(r['price'])
            if symbol == "SHIB": price = price / 1000
            return price
        if pair_name in PAIRS:
            t = PAIRS[pair_name][0]
            df = yf.download(t, period="1d", interval="1m", progress=False)
            if not df.empty: return float(df['Close'].iloc[-1])
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
            df = yf.download(t, period=period, interval=tf, auto_adjust=True, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            if df is not None and not df.empty and len(df) > 20:
                if t == "GC=F": df['Open']-=60; df['High']-=60; df['Low']-=60; df['Close']-=60
                if t == "SI=F": df['Open']-=1.5; df['High']-=1.5; df['Low']-=1.5; df['Close']-=1.5
                return df
        except: continue
    return pd.DataFrame()

col1, col2 = st.columns(2)
with col1: pair = st.selectbox("Pair Select Karo - 18 Pairs", list(PAIRS.keys()), index=0)
with col2: tf = st.selectbox("Timeframe", ("1m","5m","15m","1h","4h","1d"), index=3)

y_sym, tv_sym, pt_mult = PAIRS[pair]

if st.button("START ANALYSIS"):
    live = get_live_price(pair)
    df_raw = load_chart_fixed(y_sym, tf)
    if df_raw.empty:
        st.error(f"{pair} ka chart load nahi hua, 10 sec baad dobara dabao"); st.stop()

    df = df_raw.shift(1).dropna()
    
    mp_yahoo = float(df['Close'].iloc[-1])
    mp = live if live and live > 0 else mp_yahoo
    diff = mp - mp_yahoo
    
    c = df['Close'].astype(float)
    h = df['High'].astype(float)
    l = df['Low'].astype(float)
    o = df['Open'].astype(float)
    
    ema20 = c.ewm(span=20, adjust=False).mean()
    ema50 = c.ewm(span=50, adjust=False).mean()
    ema200 = c.ewm(span=200, adjust=False).mean()
    
    tr = pd.concat([h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.ewm(span=14, adjust=False).mean()
    
    delta = c.diff()
    gain = delta.clip(lower=0).ewm(span=14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(span=14, adjust=False).mean()
    loss_fixed = loss.mask(loss == 0, 0.00001)
    rsi = 100 - (100 / (1 + gain / loss_fixed))
    
    last = float(c.iloc[-1])
    e20 = float(ema20.iloc[-1])
    e50 = float(ema50.iloc[-1])
    e200 = float(ema200.iloc[-1])
    rsi_v = float(rsi.iloc[-1])
    atr_v = float(atr.iloc[-1])
    supp = float(l.iloc[-30:-1].min())
    res = float(h.iloc[-30:-1].max())

    # CHoCH / BOS
    recent_high = h.iloc[-15:-2].max()
    recent_low = l.iloc[-15:-2].min()
    choch_bull = last > recent_high
    choch_bear = last < recent_low
    bos_bull = e20 > e50 > e200
    bos_bear = e20 < e50 < e200
    
    # Engulfing
    prev_o = float(o.iloc[-2]); prev_c = float(c.iloc[-2]); last_o = float(o.iloc[-1])
    bull_eng = (prev_c < prev_o) and (last > last_o) and (last > prev_o) and (last_o < prev_c)
    bear_eng = (prev_c > prev_o) and (last < last_o) and (last < prev_o) and (last_o > prev_c)
    
    if tf == "1m" or tf == "5m": lookback_fvg = 100
    elif tf == "15m": lookback_fvg = 50
    elif tf == "1h": lookback_fvg = 24
    elif tf == "4h": lookback_fvg = 18
    else: lookback_fvg = 10
    
    bull_fvg=None; bear_fvg=None; bull_fvg_list=[]; bear_fvg_list=[]
    
    for i in range(len(df)-lookback_fvg, len(df)-2):
        if h.iloc[i-1] < l.iloc[i+1] and (l.iloc[i+1] - h.iloc[i-1]) > atr_v*0.25:
            fvg_low = float(h.iloc[i-1])
            fvg_high = float(l.iloc[i+1])
            
            # BUG 4 FIXED: Inner check loop stops strictly at len(df)-1 to prevent false mitigation deletion
            mitigated = False
            for j in range(i+2, len(df)-1):
                if l.iloc[j] <= fvg_low:
                    mitigated = True
                    break
            if not mitigated:
                fv = (fvg_low, fvg_high)
                bull_fvg_list.append(fv)
                bull_fvg = fv
                
        if l.iloc[i-1] > h.iloc[i+1] and (l.iloc[i-1] - h.iloc[i+1]) > atr_v*0.25:
            fvg_high = float(l.iloc[i-1])
            fvg_low = float(h.iloc[i+1])
            
            # BUG 4 FIXED: Inner check loop stops strictly at len(df)-1 to prevent false mitigation deletion
            mitigated = False
            for j in range(i+2, len(df)-1):
                if h.iloc[j] >= fvg_high:
                    mitigated = True
                    break
            if not mitigated:
                fv = (fvg_low, fvg_high)
                bear_fvg_list.append(fv)
                bear_fvg = fv
                
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
    
    if bull_fvg: score+=10; reasons.append(f"Unmitigated Bullish FVG {bull_fvg[0]:.2f}-{bull_fvg[1]:.2f} (Active Zone)")
    if bear_fvg: score-=10; reasons.append(f"Unmitigated Bearish FVG {bear_fvg[0]:.2f}-{bear_fvg[1]:.2f} (Active Zone)")
    
    if bull_ob: score+=8; reasons.append(f"Bullish OB {bull_ob[0]:.2f}-{bull_ob[1]:.2f}")
    if bear_ob: score-=8; reasons.append(f"Bearish OB {bear_ob[0]:.2f}-{bear_ob[1]:.2f}")
    reasons.append(f"Support {supp:.5f} | Resistance {res:.5f} | ATR {atr_v:.5f}")
    reasons.append(f"LIVE {mp:.5f} = {tv_sym} {mp:.5f}")
    if 45<=rsi_v<=68: reasons.append(f"RSI Neutral {rsi_v:.1f}")
    elif rsi_v>70: reasons.append(f"RSI Overbought {rsi_v:.1f}")
    else: reasons.append(f"RSI Oversold {rsi_v:.1f}")

    buy_score=max(5,min(95,score)); sell_score=100-buy_score
    base_dist = max(mp*0.007, atr_v*2.8)
    def pts(d): return int(abs(d)*pt_mult)
    
    if buy_score>=60:
        sl_short = mp - base_dist; sl_long = min(sl_short, supp - atr_v*0.5)
        tp_s1 = mp + base_dist*1.2; tp_s2 = mp + base_dist*2.0
        tp_l1 = mp + base_dist*2.0; tp_l2 = mp + base_dist*3.5; tp_l3 = mp + base_dist*5.5
          
