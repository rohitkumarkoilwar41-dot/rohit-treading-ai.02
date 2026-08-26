import streamlit as st, yfinance as yf, pandas as pd, plotly.graph_objects as go, requests, os, time
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

st.title("🟨 JANTA AI - ALL CRYPTO + GOLD - V3 FIXED 100%")

# === TELEGRAM CONFIG ===
TELEGRAM_BOT_TOKEN = "8868544850:AAEs-Km9Git1urwPCQ68TH_k3ah_basTOI4"
TELEGRAM_CHAT_ID = "7071872872"

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Telegram Error: {e}")
        return False

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
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        if "XAUUSD" in pair_name:
            r=requests.get("https://api.gold-api.com/price/XAU", timeout=5, headers=headers).json()
            return float(r['price'])
        if "XAGUSD" in pair_name:
            r=requests.get("https://api.gold-api.com/price/XAG", timeout=5, headers=headers).json()
            return float(r['price'])
        if "-USD" in pair_name and "XAU" not in pair_name and "XAG" not in pair_name and "EUR" not in pair_name and "GBP" not in pair_name and "USDJPY" not in pair_name and "AUDUSD" not in pair_name:
            symbol = pair_name.split("-")[0]
            binance_symbol = f"{symbol}USDT"
            if symbol=="SHIB": binance_symbol="1000SHIBUSDT"
            r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={binance_symbol}", timeout=5, headers=headers).json()
            price=float(r['price'])
            if symbol=="SHIB": price=price/1000
            return price
        if pair_name in PAIRS:
            t=PAIRS[pair_name][0]
            df=yf.download(t, period="1d", interval="1m", progress=False)
            if not df.empty: return float(df['Close'].iloc[-1])
    except: return None
    return None

def fetch_binance_klines(symbol, interval, limit=1000):
    try:
        tf_map = {"1m":"1m", "5m":"5m", "15m":"15m", "1h":"1h", "4h":"4h", "1d":"1d"}
        b_interval = tf_map.get(interval, "15m")
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={b_interval}&limit={limit}"
        r = requests.get(url, timeout=10, headers={"User-Agent":"Mozilla/5.0"}).json()
        if not isinstance(r, list) or len(r)==0:
            return pd.DataFrame()
        df = pd.DataFrame(r, columns=["open_time","Open","High","Low","Close","Volume","close_time","qav","trades","taker_base","taker_quote","ignore"])
        df["Open"] = df["Open"].astype(float)
        df["High"] = df["High"].astype(float)
        df["Low"] = df["Low"].astype(float)
        df["Close"] = df["Close"].astype(float)
        df["Volume"] = df["Volume"].astype(float)
        df.index = pd.to_datetime(df["close_time"], unit='ms')
        return df[["Open","High","Low","Close","Volume"]]
    except Exception as e:
        print(f"Binance Klines Error {symbol}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=40)
def load_chart_fixed(ticker, tf):
    crypto_map = {
        "BTC-USD": "BTCUSDT",
        "ETH-USD": "ETHUSDT", 
        "SOL-USD": "SOLUSDT",
        "XRP-USD": "XRPUSDT",
        "DOGE-USD": "DOGEUSDT",
        "SHIB-USD": "1000SHIBUSDT"
    }
    if ticker in crypto_map:
        df = fetch_binance_klines(crypto_map[ticker], tf, limit=1000)
        if not df.empty and len(df)>20:
            if ticker=="SHIB-USD":
                df["Open"]=df["Open"]/1000
                df["High"]=df["High"]/1000
                df["Low"]=df["Low"]/1000
                df["Close"]=df["Close"]/1000
            return df
    tickers_to_try = [ticker]
    if "XAUUSD" in ticker: tickers_to_try = ["XAUUSD=X", "GC=F"]
    if "XAGUSD" in ticker: tickers_to_try = ["XAGUSD=X", "SI=F"]
    for t in tickers_to_try:
        try:
            period = "7d" if tf=="1m" else "10d" if tf in ["5m","15m","1h"] else "60d"
            df=yf.download(t, period=period, interval=tf, auto_adjust=True, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns=df.columns.get_level_values(0)
            if df is not None and not df.empty and len(df)>20:
                if t=="GC=F": df['Open']-=60; df['High']-=60; df['Low']-=60; df['Close']-=60
                if t=="SI=F": df['Open']-=1.5; df['High']-=1.5; df['Low']-=1.5; df['Close']-=1.5
                return df
        except: continue
    return pd.DataFrame()

def calculate_analysis(y_sym, tv_sym, pt_mult, pair, tf):
    live = get_live_price(pair)
    df = load_chart_fixed(y_sym, tf)
    if df.empty:
        return None, f"{pair} ka chart load nahi hua, 10 sec baad dobara dabao"
    mp_yahoo = float(df['Close'].iloc[-1])
    mp = live if live and live>0 else mp_yahoo
    diff = mp - mp_yahoo
    df['Close']+=diff; df['High']+=diff; df['Low']+=diff; df['Open']+=diff
    c,h,l,o=df['Close'].astype(float),df['High'].astype(float),df['Low'].astype(float),df['Open'].astype(float)
    vol = df['Volume'].astype(float) if 'Volume' in df.columns else pd.Series(1, index=c.index)
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
    if pd.isna(atr_v) or atr_v==0: atr_v = float((h.iloc[-14:].min() - l.iloc[-14:].min())/14) if False else float((h.iloc[-14:].max() - l.iloc[-14:].min())/14)
    supp=float(l.iloc[-30:-1].min()); res=float(h.iloc[-30:-1].max())
    recent_high=h.iloc[-15:-2].max(); recent_low=l.iloc[-15:-2].min()
    choch_bull=last>recent_high; choch_bear=last<recent_low
    bos_bull=e20>e50>e200; bos_bear=e20<e50<e200
    prev_o=float(o.iloc[-2]); prev_c=float(c.iloc[-2]); last_o=float(o.iloc[-1])
    bull_eng=(prev_c<prev_o) and (last>last_o) and (last>prev_o) and (last_o<prev_c)
    bear_eng=(prev_c>prev_o) and (last<last_o) and (last<prev_o) and (last_o>prev_c)

    # === FIXED EQH/EQL - Latest Wala ===
    liq_bull=False; liq_bear=False; eqh_level=None; eql_level=None
    look_liq = 30
    highs_30 = h.iloc[-look_liq-5:-5]
    lows_30 = l.iloc[-look_liq-5:-5]
    tol = atr_v * 0.15
    eqh_candidates = []
    for i in range(len(highs_30)-1):
        for j in range(i+1, len(highs_30)):
            if abs(float(highs_30.iloc[i]) - float(highs_30.iloc[j])) < tol:
                eqh_candidates.append(float(highs_30.iloc[i]))
    if eqh_candidates:
        eqh_level = eqh_candidates[-1]
        if h.iloc[-2] > eqh_level and c.iloc[-1] < eqh_level and last < eqh_level:
            liq_bear = True
    eql_candidates = []
    for i in range(len(lows_30)-1):
        for j in range(i+1, len(lows_30)):
            if abs(float(lows_30.iloc[i]) - float(lows_30.iloc[j])) < tol:
                eql_candidates.append(float(lows_30.iloc[i]))
    if eql_candidates:
        eql_level = eql_candidates[-1]
        if l.iloc[-2] < eql_level and c.iloc[-1] > eql_level and last > eql_level:
            liq_bull = True

    if tf == "1m" or tf == "5m": lookback_fvg = 100
    elif tf == "15m": lookback_fvg = 50
    elif tf == "1h": lookback_fvg = 24
    elif tf == "4h": lookback_fvg = 18
    else: lookback_fvg = 10
    bull_fvg=None; bear_fvg=None; bull_fvg_list=[]; bear_fvg_list=[]
    min_fvg_size = atr_v * 0.5
    for i in range(len(df)-lookback_fvg, len(df)-2):
        if i < 1: continue
        if h.iloc[i-1] < l.iloc[i+1] and (l.iloc[i+1] - h.iloc[i-1]) > min_fvg_size:
            fvg_low = float(h.iloc[i-1]); fvg_high = float(l.iloc[i+1])
            fvg_mid = (fvg_low + fvg_high)/2
            if fvg_low <= last <= fvg_high: continue
            if abs(last - fvg_low) < atr_v*0.3 or abs(last - fvg_high) < atr_v*0.3: continue
            mitigated=False
            for j in range(i+2, len(df)-1):
                if l.iloc[j] <= fvg_mid:
                    mitigated=True; break
            if not mitigated:
                fv=(fvg_low, fvg_high); bull_fvg_list.append(fv); bull_fvg=fv
        if l.iloc[i-1] > h.iloc[i+1] and (l.iloc[i-1] - h.iloc[i+1]) > min_fvg_size:
            fvg_low = float(h.iloc[i+1]); fvg_high = float(l.iloc[i-1])
            fvg_mid = (fvg_low + fvg_high)/2
            if fvg_low <= last <= fvg_high: continue
            if abs(last - fvg_low) < atr_v*0.3 or abs(last - fvg_high) < atr_v*0.3: continue
            mitigated=False
            for j in range(i+2, len(df)-1):
                if h.iloc[j] >= fvg_mid:
                    mitigated=True; break
            if not mitigated:
                fv=(fvg_low, fvg_high); bear_fvg_list.append(fv); bear_fvg=fv
    bull_ob=None; bear_ob=None
    for i in range(len(df)-15,len(df)-2):
        if c.iloc[i]<o.iloc[i] and c.iloc[i+1]>o.iloc[i+1] and c.iloc[i+2]>h.iloc[i]: bull_ob=(float(l.iloc[i]),float(h.iloc[i]))
        if c.iloc[i]>o.iloc[i] and c.iloc[i+1]<o.iloc[i+1] and c.iloc[i+2]<l.iloc[i]: bear_ob=(float(l.iloc[i]),float(h.iloc[i]))

    # === NEW RULE 11: FIBONACCI GOLDEN ZONE ===
    fib_bull=False; fib_bear=False; fib_level=None
    try:
        swing_high = float(h.iloc[-35:-5].max())
        swing_low = float(l.iloc[-35:-5].min())
        swing_diff = swing_high - swing_low
        if swing_diff > 0:
            fib_05 = swing_high - swing_diff*0.5
            fib_618 = swing_high - swing_diff*0.618
            fib_786 = swing_high - swing_diff*0.786
            # Discount zone = below 0.5 (sasta)
            # Golden Pocket = 0.618-0.786
            if fib_786 <= last <= fib_05:
                fib_bull = True
                fib_level = fib_618
                if fib_786 <= last <= fib_618:
                    fib_level = fib_618 # Golden Pocket exact
            # Premium zone for sell
            fib_premium_low = swing_low + swing_diff*0.5
            fib_premium_high = swing_low + swing_diff*0.786
            if fib_premium_low <= last <= fib_premium_high:
                fib_bear = True
                if fib_level is None:
                    fib_level = swing_low + swing_diff*0.618
    except:
        fib_bull=False; fib_bear=False

    # === NEW RULE 14: VOLUME POC ===
    poc_bull=False; poc_bear=False; poc_level=None
    try:
        last_30_h = h.iloc[-30:]; last_30_l = l.iloc[-30:]; last_30_v = vol.iloc[-30:]
        price_min = float(last_30_l.min()); price_max = float(last_30_h.max())
        if price_max > price_min:
            bins = 20
            bin_edges = np.linspace(price_min, price_max, bins+1)
            bin_vol = np.zeros(bins)
            bin_centers = []
            for b in range(bins):
                low_e = bin_edges[b]; high_e = bin_edges[b+1]
                center = (low_e+high_e)/2; bin_centers.append(center)
                # Sum volume where close in bin
                mask = (c.iloc[-30:] >= low_e) & (c.iloc[-30:] < high_e)
                bin_vol[b] = float(last_30_v[mask].sum()) if mask.any() else 0
            max_bin = int(np.argmax(bin_vol))
            poc_level = float(bin_centers[max_bin])
            # If price near POC within 0.3 ATR
            if abs(last - poc_level) < atr_v*0.8:
                # Bounce logic: if last above POC and recent low touched POC -> bullish
                if last > poc_level and l.iloc[-3:].min() <= poc_level + atr_v*0.2:
                    poc_bull = True
                if last < poc_level and h.iloc[-3:].max() >= poc_level - atr_v*0.2:
                    poc_bear = True
                # Even if not exact bounce, proximity gives weight
                if not poc_bull and not poc_bear:
                    if last > poc_level:
                        poc_bull = True
                    else:
                        poc_bear = True
    except:
        poc_bull=False; poc_bear=False

    # === FIXED 100% SCORING MODEL ===
    # EMA=4, BOS=4, CHoCH=10, Engulfing=10, Liquidity=30 KING, Fib=16, OB=16, POC=10
    buy_points = 0; sell_points = 0
    reasons=[]

    # EMA Trend 4 point
    if last>e20>e50:
        buy_points+=4; reasons.append(f"✅ EMA Bullish +4 - Price {last:.2f} > EMA20 {e20:.2f} > EMA50 {e50:.2f}")
    elif last<e20<e50:
        sell_points+=4; reasons.append(f"✅ EMA Bearish +4 - Price {last:.2f} < EMA20 {e20:.2f} < EMA50 {e50:.2f}")
    else:
        reasons.append(f"⚪ EMA Neutral 0 - No clear trend")

    # BOS 4 point
    if bos_bull:
        buy_points+=4; reasons.append(f"✅ BOS Bullish +4 - EMA20>EMA50>EMA200 ({e200:.2f})")
    elif bos_bear:
        sell_points+=4; reasons.append(f"✅ BOS Bearish +4 - EMA20<EMA50<EMA200")
    else:
        reasons.append(f"⚪ BOS Neutral 0")

    # CHoCH 10 point
    if choch_bull:
        buy_points+=10; reasons.append(f"✅ CHoCH Bullish +10 - Swing High Break {recent_high:.2f}")
    if choch_bear:
        sell_points+=10; reasons.append(f"✅ CHoCH Bearish +10 - Swing Low Break {recent_low:.2f}")

    # Engulfing 10 point
    if bull_eng:
        buy_points+=10; reasons.append("✅ Bullish Engulfing +10 - Strong Buy Signal")
    if bear_eng:
        sell_points+=10; reasons.append("✅ Bearish Engulfing +10 - Strong Sell Signal")

    # Liquidity Sweep 30 KING
    if liq_bull:
        buy_points+=30; reasons.append(f"🔥 Bullish Liquidity Sweep +30 KING - EQL {eql_level:.2f} se reversal (Stop-Hunt)")
    if liq_bear:
        sell_points+=30; reasons.append(f"🔥 Bearish Liquidity Sweep +30 KING - EQH {eqh_level:.2f} se reversal (Stop-Hunt)")

    # Fibonacci 16
    if fib_bull:
        buy_points+=16; reasons.append(f"✅ Fibonacci Golden Zone +16 - Price Golden Pocket {fib_level:.2f} me (Discount)")
    if fib_bear:
        sell_points+=16; reasons.append(f"✅ Fibonacci Premium Zone +16 - Price Premium {fib_level:.2f} me")

    # Order Block 16 (OB+FVG combine as OB per photo)
    if bull_ob or bull_fvg:
        buy_points+=16
        if bull_ob: reasons.append(f"✅ Bullish Order Block +16 - {bull_ob[0]:.2f}-{bull_ob[1]:.2f} (1H OB)")
        if bull_fvg: reasons.append(f"✅ Bullish FVG +16 - {bull_fvg[0]:.2f}-{bull_fvg[1]:.2f}")
    if bear_ob or bear_fvg:
        sell_points+=16
        if bear_ob: reasons.append(f"✅ Bearish Order Block +16 - {bear_ob[0]:.2f}-{bear_ob[1]:.2f}")
        if bear_fvg: reasons.append(f"✅ Bearish FVG +16 - {bear_fvg[0]:.2f}-{bear_fvg[1]:.2f}")

    # POC 10
    if poc_bull:
        buy_points+=10; reasons.append(f"✅ Volume POC Bounce +10 - POC Level {poc_level:.2f} se bounce")
    if poc_bear:
        sell_points+=10; reasons.append(f"✅ Volume POC Rejection +10 - POC Level {poc_level:.2f} se rejection")

    # Jackpot Detection
    is_jackpot_buy = (liq_bull and (fib_bull or poc_bull) and (bull_ob or bull_fvg))
    is_jackpot_sell = (liq_bear and (fib_bear or poc_bear) and (bear_ob or bear_fvg))

    if is_jackpot_buy:
        reasons.append(f"💎 JACKPOT BUY - Liquidity Sweep + Fib + OB + POC ek saath! 30+16+16+10 = {buy_points}%")
    if is_jackpot_sell:
        reasons.append(f"💎 JACKPOT SELL - Liquidity Sweep + Fib + OB + POC ek saath! 30+16+16+10 = {sell_points}%")

    # Fake Signal Filter
    if buy_points>0 and buy_points<30:
        reasons.append(f"⚠️ Fake Signal Filter - Sirf {buy_points}% Buy hai (Top pe fasne se bacho) - HOLD")
    if sell_points>0 and sell_points<30:
        reasons.append(f"⚠️ Fake Signal Filter - Sirf {sell_points}% Sell hai - HOLD")

    reasons.append(f"LIVE {last:.5f} = {tv_sym} {last:.5f} | ATR {atr_v:.2f}")
    if 45<=rsi_v<=68: reasons.append(f"RSI Neutral {rsi_v:.1f}")
    elif rsi_v>70: reasons.append(f"RSI Overbought {rsi_v:.1f} - Top ka khatra")
    else: reasons.append(f"RSI Oversold {rsi_v:.1f} - Bottom ka mauka")

    # === NO MORE bull_count>=6 BYPASS - DELETED PER REQUIREMENT ===
    # Old filter: if bull_count>=6 and bear_count==0: score=100 -> REMOVED

    buy_score = max(0, min(100, buy_points))
    sell_score = max(0, min(100, sell_points))

    # If both sides present, keep actual points (e.g., 72% vs 28% not forced 100)
    # For display compatibility, ensure at least one side is visible
    base_dist = max(mp*0.004, atr_v*1.5)
    def pts(d): return int(abs(d)*pt_mult)
    result = {
        "df": df, "c":c,"h":h,"l":l,"o":o,
        "ema20":ema20,"ema50":ema50,
        "mp":mp,"last":last,"diff":diff,"atr_v":atr_v,"supp":supp,"res":res,
        "buy_score":buy_score,"sell_score":sell_score,
        "buy_points":buy_points,"sell_points":sell_points,
        "bull_fvg_list":bull_fvg_list,"bear_fvg_list":bear_fvg_list,
        "reasons":reasons,"bull_ob":bull_ob,"bear_ob":bear_ob,
        "bull_fvg":bull_fvg,"bear_fvg":bear_fvg,
        "liq_bull":liq_bull,"liq_bear":liq_bear,
        "eqh_level":eqh_level,"eql_level":eql_level,
        "fib_level":fib_level,"poc_level":poc_level,
        "fib_bull":fib_bull,"fib_bear":fib_bear,
        "poc_bull":poc_bull,"poc_bear":poc_bear,
        "is_jackpot_buy":is_jackpot_buy,"is_jackpot_sell":is_jackpot_sell,
        "base_dist":base_dist,"pts":pts,
        "y_sym":y_sym,"tv_sym":tv_sym,"pair":pair,"tf":tf
    }
    return result, None

# --- SESSION STATE ---
if "tracker_on" not in st.session_state: st.session_state.tracker_on=False
if "tracker_pair" not in st.session_state: st.session_state.tracker_pair=None
if "tracker_tf" not in st.session_state: st.session_state.tracker_tf=None

col1,col2=st.columns(2)
with col1: pair=st.selectbox("Pair Select Karo - 18 Pairs", list(PAIRS.keys()), index=0)
with col2: tf=st.selectbox("Timeframe", ("1m","5m","15m","1h","4h","1d"), index=3)

y_sym, tv_sym, pt_mult = PAIRS[pair]

if st.button("START ANALYSIS"):
    result, err = calculate_analysis(y_sym, tv_sym, pt_mult, pair, tf)
    if err:
        st.error(err); st.stop()
    st.session_state.last_result = result
    st.session_state.last_pair = pair
    st.session_state.last_tf = tf

cA,cB = st.columns(2)
with cA:
    if st.button("🔔 Turn On Live Notification Tracker"):
        st.session_state.tracker_on = True
        st.session_state.tracker_pair = pair
        st.session_state.tracker_tf = tf
        st.session_state.last_result = None
        st.rerun()
with cB:
    if st.button("🔕 Turn Off Tracker"):
        st.session_state.tracker_on = False
        st.rerun()

if st.session_state.tracker_on:
    live_price = get_live_price(st.session_state.tracker_pair)
    y_sym_t, tv_sym_t, pt_mult_t = PAIRS[st.session_state.tracker_pair]
    result_t, err_t = calculate_analysis(y_sym_t, tv_sym_t, pt_mult_t, st.session_state.tracker_pair, st.session_state.tracker_tf)
    if result_t:
        mp_live = result_t["mp"]; buy_s = result_t["buy_score"]; sell_s = result_t["sell_score"]
        is_jackpot = result_t.get("is_jackpot_buy", False) or result_t.get("is_jackpot_sell", False)
        # Threshold 70 for jackpot, 50 for normal
        threshold = 70 if is_jackpot else 50
        if buy_s >= threshold and buy_s > sell_s:
            tg_status = f"🚀 BUY {buy_s}% - JACKPOT" if is_jackpot else f"🚀 BUY {buy_s}%"
            tg_emoji = "💎" if is_jackpot else "🚀"
        elif sell_s >= threshold and sell_s > buy_s:
            tg_status = f"📉 SELL {sell_s}% - JACKPOT" if is_jackpot else f"📉 SELL {sell_s}%"
            tg_emoji = "💎" if is_jackpot else "📉"
        else:
            tg_status = f"⏸️ HOLD - BUY {buy_s}% | SELL {sell_s}%"
            tg_emoji = "⏸️"

        st.markdown(f"<div style='background:#111; border:2px solid #FFD700; padding:10px; border-radius:10px; text-align:center; color:#FFD700;'>🔔 Tracker ON - {st.session_state.tracker_pair} {st.session_state.tracker_tf} | {tg_status} | Live {mp_live:.5f}</div>", unsafe_allow_html=True)

        # Send only if BUY/SELL >=50 (or jackpot)
        if buy_s >= 50 or sell_s >= 50:
            dt_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
            t_pair = st.session_state.tracker_pair
            t_tf = st.session_state.tracker_tf
            sl_show = f"{result_t['supp']:.2f}" if buy_s > sell_s else f"{result_t['res']:.2f}"

            msg_lines = []
            msg_lines.append(tg_emoji + " " + t_pair + " | " + t_tf)
            msg_lines.append(tg_status)
            if is_jackpot:
                msg_lines.append("💎 JACKPOT: 30+16+16+10 Combo!")
            msg_lines.append("Price: " + str(round(mp_live,2)) + " | SL: " + sl_show)
            msg_lines.append("Buy%: " + str(buy_s) + " | Sell%: " + str(sell_s))
            msg_lines.append("Time: " + dt_now)
            msg_lines.append("App: rohit-treading-ai-02.streamlit.app")
            tg_text = chr(10).join(msg_lines)

            sent = send_telegram_message(tg_text)
            if sent:
                st.toast("Telegram Sent: " + tg_status, icon="✅")
            else:
                st.toast("Telegram Failed", icon="❌")
            components.html("<div style='background:#111; border:1px solid #0f0; padding:8px; border-radius:8px; color:#0f0; font-size:11px;'>Telegram: " + ("Sent" if sent else "Failed") + " | " + dt_now + "<br>" + tg_status + "</div>", height=80)

if "last_result" in st.session_state and st.session_state.last_result:
    result = st.session_state.last_result
    pair = st.session_state.last_pair
    tf = st.session_state.last_tf
    df = result["df"]; c=result["c"]; h=result["h"]; l=result["l"]; o=result["o"]
    ema20=result["ema20"]; ema50=result["ema50"]
    mp=result["mp"]; last=result["last"]; diff=result["diff"]; atr_v=result["atr_v"]
    supp=result["supp"]; res=result["res"]
    buy_score=result["buy_score"]; sell_score=result["sell_score"]
    buy_points=result.get("buy_points", buy_score); sell_points=result.get("sell_points", sell_score)
    bull_fvg_list=result["bull_fvg_list"]; bear_fvg_list=result["bear_fvg_list"]
    reasons=result["reasons"]; base_dist=result["base_dist"]; pts=result["pts"]
    y_sym=result["y_sym"]; tv_sym=result["tv_sym"]
    is_jackpot_buy=result.get("is_jackpot_buy", False); is_jackpot_sell=result.get("is_jackpot_sell", False)

    sl_plot=None; tp1_plot=None; tp2_plot=None
    # New Neutral Logic: if both <50 or difference <10 and no jackpot
    is_neutral = False
    if not is_jackpot_buy and not is_jackpot_sell:
        if max(buy_score, sell_score) < 50:
            is_neutral = True
        elif abs(buy_score - sell_score) <= 10 and max(buy_score, sell_score) < 70:
            is_neutral = True

    if is_neutral:
        st.markdown(f"""<div style='background:linear-gradient(135deg,#222200,#666600); border:3px solid #FFD700; padding:22px; border-radius:16px;'><div style='color:#FFD700; font-size:28px; font-weight:900; text-align:center;'>⏸️ HOLD / NEUTRAL {pair} @ {mp:.5f}</div><div style='color:#fff; text-align:center; margin-top:10px; font-size:14px;'>BUY {buy_score}% | SELL {sell_score}% - Market Range Me Hai, Wait Karo (Fake Signal Filter Active)</div><div style='color:#aaa; text-align:center; margin-top:8px; font-size:12px;'>EMA 4 + BOS 4 + CHoCH 10 + Engulfing 10 = {buy_score+ sell_score if buy_score>sell_score else buy_score+ sell_score}% Only - 75%+ needed</div></div>""", unsafe_allow_html=True)
        sl_plot, tp1_plot, tp2_plot = None, None, None
    elif buy_score > sell_score:
        sl_short = mp - base_dist; sl_long = min(sl_short, supp - atr_v*0.5)
        tp_s1 = mp + base_dist*1.2; tp_s2 = mp + base_dist*2.0
        tp_l1 = mp + base_dist*2.0; tp_l2 = mp + base_dist*3.5; tp_l3 = mp + base_dist*5.5
        jackpot_badge = " 💎 JACKPOT - BOTTOM PRICE" if is_jackpot_buy else ""
        st.markdown(f"""<div style='background:linear-gradient(135deg,#002200,#00a336); border:3px solid #00ff88; padding:22px; border-radius:16px;'><div style='color:#fff; font-size:28px; font-weight:900; text-align:center;'>🚀 BUY {pair} @ {mp:.5f}{jackpot_badge}</div><div style='color:#00ff88; text-align:center; margin-top:8px; font-size:16px; font-weight:700;'>BUY Score {buy_score}% = 30+16+16+10 Combo | SELL {sell_score}%</div><div style='display:flex; gap:10px; margin-top:14px;'><div style='flex:1; background:#000; border:2px solid #ffcc00; border-radius:12px; padding:12px; text-align:center;'><div style='color:#ffcc00; font-weight:900;'>⚡ SHORT SL</div><div style='color:#fff; font-size:12px; margin-top:6px;'>SL {sl_short:.5f} ({pts(mp-sl_short)} pt)<br>TP1 {tp_s1:.5f}<br>TP2 {tp_s2:.5f}</div></div><div style='flex:1; background:#000; border:2px solid #00ff88; border-radius:12px; padding:12px; text-align:center;'><div style='color:#00ff88; font-weight:900;'>🚀 LONG (SL Minimizer 150-200pt)</div><div style='color:#fff; font-size:12px; margin-top:6px;'>SL {sl_long:.5f}<br>TP1 {tp_l1:.5f}<br>TP2 {tp_l2:.5f}<br>TP3 {tp_l3:.5f}</div></div></div></div>""", unsafe_allow_html=True)
        sl_plot,tp1_plot,tp2_plot = sl_long, tp_l1, tp_l2
    else:
        sl_short = mp + base_dist; sl_long = max(sl_short, res + atr_v*0.5)
        tp_s1 = mp - base_dist*1.2; tp_s2 = mp - base_dist*2.0
        tp_l1 = mp - base_dist*2.0; tp_l2 = mp - base_dist*3.5; tp_l3 = mp - base_dist*5.5
        jackpot_badge = " 💎 JACKPOT - TOP PRICE" if is_jackpot_sell else ""
        st.markdown(f"""<div style='background:linear-gradient(135deg,#330000,#cc0000); border:3px solid #ff4444; padding:22px; border-radius:16px;'><div style='color:#fff; font-size:28px; font-weight:900; text-align:center;'>📉 SELL {pair} @ {mp:.5f}{jackpot_badge}</div><div style='color:#ff8888; text-align:center; margin-top:8px; font-size:16px; font-weight:700;'>SELL Score {sell_score}% = 30+16+16+10 Combo | BUY {buy_score}%</div><div style='display:flex; gap:10px; margin-top:14px;'><div style='flex:1; background:#000; border:2px solid #ffcc00; border-radius:12px; padding:12px; text-align:center;'><div style='color:#ffcc00; font-weight:900;'>⚡ SHORT</div><div style='color:#fff; font-size:12px; margin-top:6px;'>SL {sl_short:.5f}<br>TP1 {tp_s1:.5f}<br>TP2 {tp_s2:.5f}</div></div><div style='flex:1; background:#000; border:2px solid #ff8888; border-radius:12px; padding:12px; text-align:center;'><div style='color:#ff8888; font-weight:900;'>📉 LONG</div><div style='color:#fff; font-size:12px; margin-top:6px;'>SL {sl_long:.5f}<br>TP1 {tp_l1:.5f}<br>TP2 {tp_l2:.5f}<br>TP3 {tp_l3:.5f}</div></div></div></div>""", unsafe_allow_html=True)
        sl_plot,tp1_plot,tp2_plot = sl_long, tp_s1, tp_s2

    if sl_plot is None:
        saved_file = save_data(pair, mp, 0, 0, 0, buy_score, sell_score)
    else:
        saved_file = save_data(pair, mp, sl_plot, tp1_plot, tp2_plot, buy_score, sell_score)
    st.success(f"✅ Data Save Ho Gaya - {saved_file} | BUY {buy_score}% | SELL {sell_score}%")
    st.markdown("### 📁 Last 5 Saved")
    if os.path.exists("trading_history.csv"):
        st.dataframe(pd.read_csv("trading_history.csv").tail(5), use_container_width=True)
    c1,c2,c3=st.columns(3)
    c1.metric("BUY %", f"{buy_score}% (Fix 100 Model)"); c2.metric("SELL %", f"{sell_score}%"); c3.metric("LIVE", f"{mp:.5f}", delta=f"{diff:+.5f}")
    with st.expander("📝 AI THESIS - Reasons (Fixed 100% Model)", expanded=True):
        for r in reasons: st.write(r)
    with st.expander("🔍 Fixed 100% Model Breakdown"):
        st.write(f"EMA Trend: 4 point | BOS: 4 point | CHoCH: 10 point | Engulfing: 10 point")
        st.write(f"Liquidity Sweep KING: 30 point | Fibonacci Golden Zone: 16 point | Order Block: 16 point | Volume POC: 10 point")
        st.write(f"Total = 4+4+10+10+30+16+16+10 = 100%")
        st.write(f"Current BUY Points = {buy_points} | SELL Points = {sell_points}")
        if result.get("fib_level"): st.write(f"Fib Level: {result['fib_level']:.2f}")
        if result.get("poc_level"): st.write(f"POC Level: {result['poc_level']:.2f}")
        if result.get("eqh_level"): st.write(f"EQH Level: {result['eqh_level']:.2f}")
        if result.get("eql_level"): st.write(f"EQL Level: {result['eql_level']:.2f}")
    st.markdown(f"### 📈 TradingView {tv_sym} Live")
    components.iframe(f"https://s.tradingview.com/widgetembed/?symbol={tv_sym}&interval={TV_MAP[tf]}&theme=dark&style=1&timezone=Asia/Kolkata", height=550)
    fig=go.Figure(data=[go.Candlestick(x=df.index, open=o, high=h, low=l, close=c, name="Price")])
    fig.add_trace(go.Scatter(x=df.index, y=ema20, line=dict(color='#FFD700', width=1.5), name='EMA20'))
    fig.add_trace(go.Scatter(x=df.index, y=ema50, line=dict(color='#FF8C00', width=1.5), name='EMA50'))
    fig.add_hline(y=last,line_color="white",line_dash="dash",annotation_text=f"LIVE {last:.2f}")
    if result.get("fib_level"): fig.add_hline(y=result["fib_level"], line_color="cyan", line_dash="dot", annotation_text=f"Fib 0.618 {result['fib_level']:.2f}")
    if result.get("poc_level"): fig.add_hline(y=result["poc_level"], line_color="purple", line_dash="dot", annotation_text=f"POC {result['poc_level']:.2f}")
    if result.get("eql_level"): fig.add_hline(y=result["eql_level"], line_color="green", line_dash="dash", annotation_text=f"EQL {result['eql_level']:.2f}")
    if result.get("eqh_level"): fig.add_hline(y=result["eqh_level"], line_color="red", line_dash="dash", annotation_text=f"EQH {result['eqh_level']:.2f}")
    if sl_plot is not None:
        fig.add_hline(y=sl_plot, line_color="red", line_dash="dash", annotation_text=f"SL {sl_plot:.2f}")
        fig.add_hline(y=tp1_plot, line_color="green", line_dash="dot", annotation_text=f"TP1 {tp1_plot:.2f}")
        fig.add_hline(y=tp2_plot, line_color="green", line_dash="dot", annotation_text=f"TP2 {tp2_plot:.2f}")
    for fv in bull_fvg_list[-3:]: fig.add_hrect(y0=fv[0], y1=fv[1], fillcolor="green", opacity=0.18, line_width=0)
    for fv in bear_fvg_list[-3:]: fig.add_hrect(y0=fv[0], y1=fv[1], fillcolor="red", opacity=0.18, line_width=0)
    fig.update_layout(template="plotly_dark",height=600,xaxis_rangeslider_visible=False,dragmode='pan',paper_bgcolor='black',plot_bgcolor='black')
    st.plotly_chart(fig,use_container_width=True,config={'scrollZoom':True, 'displayModeBar':True})

if st.session_state.tracker_on:
    time.sleep(60)
    st.rerun()
