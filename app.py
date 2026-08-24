import streamlit as st, yfinance as yf, pandas as pd, plotly.graph_objects as go, requests, os
import numpy as np
from datetime import datetime, time
import streamlit.components.v1 as components
import time as t_delay
from concurrent.futures import ThreadPoolExecutor

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

# --- 🛰️ TELEGRAM USER CREDENTIALS (DIARY DATA LOCKED) ---
TELEGRAM_TOKEN = "8868544850:AAEs-Km9Git1urwPCQ68TH_k3ah_basTOI4"
TELEGRAM_CHAT_ID = "7071872872"

def send_telegram_alert(pair_name, signal_type, entry_p, sl_p, tp1_p, tp2_p, reason_txt):
    try:
        emoji = "🚀" if "BUY" in signal_type else "📉"
        msg = (
            f"🎯 *JANTA AI - 100% JACKPOT ALERT*\n\n"
            f"*Pair:* `{pair_name}`\n"
            f"*Signal:* {emoji} `{signal_type} (100% CONFIRMED)`\n"
            f"*SMC Reason:* {reason_txt}\n\n"
            f"🎯 *Trading Plan:*\n"
            f"• *Entry:* {entry_p:.5f}\n"
            f"• *SL:* {sl_p:.5f}\n"
            f"• *TP1:* {tp1_p:.5f}\n"
            f"• *TP2:* {tp2_p:.5f}\n\n"
            f"_[यह जैकपॉट अलर्ट 1 Second Parallel Scanner द्वारा भेजा गया है]_"
        )
        url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except:
        pass

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
        df_new.to_csv(file, index=False)
        return file
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
            r=requests.get("https://gold-api.com", timeout=5, headers=headers).json()
            return float(r['price'])
        if "XAGUSD" in pair_name:
            r=requests.get("https://gold-api.com", timeout=5, headers=headers).json()
            return float(r['price'])
        if "-USD" in pair_name and "XAU" not in pair_name and "XAG" not in pair_name and "EUR" not in pair_name and "GBP" not in pair_name and "USDJPY" not in pair_name and "AUDUSD" not in pair_name:
            symbol = pair_name.split("-")
            binance_symbol = f"{symbol[0]}USDT"
            if symbol[0]=="SHIB": binance_symbol="1000SHIBUSDT"
            r=requests.get(f"https://binance.com{binance_symbol}", timeout=5, headers=headers).json()
            price=float(r['price'])
            if symbol[0]=="SHIB": price=price/1000
            return price
        if pair_name in PAIRS:
            t=PAIRS[pair_name][0]
            df=yf.download(t, period="1d", interval="1m", progress=False)
            if not df.empty: return float(df['Close'].iloc[-1])
    except: return None
    return None

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

# --- 🛰️ CORE SMC/VOLUME CHECKLIST ENGINE (ALL 15 RULES BUILT-IN) ---
def core_janta_engine(pair_key, tf_val):
    y_sym, tv_sym, pt_mult = PAIRS[pair_key]
    live = get_live_price(pair_key)
    df = load_chart_fixed(y_sym, tf_val)
    if df.empty: return None

    mp_yahoo = float(df['Close'].iloc[-1])
    mp = live if live and live>0 else mp_yahoo
    diff = mp - mp_yahoo
    df['Close']+=diff; df['High']+=diff; df['Low']+=diff; df['Open']+=diff

    c,h,l,o=df['Close'].astype(float),df['High'].astype(float),df['Low'].astype(float),df['Open'].astype(float)
    v_series = df['Volume'].astype(float) if 'Volume' in df.columns else pd.Series(100, index=df.index)
    
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
    bos_bull=e20>e50>e200; bos_bear=e20<e50<e200

    # Rule 11 (Fibonacci Matrix)
    fib_high = h.iloc[-30:].max(); fib_low = l.iloc[-30:].min()
    fib_diff = fib_high - fib_low
    fib_50 = fib_high - (fib_diff * 0.5)
    in_discount = last <= fib_50
    in_premium = last >= fib_50

    # Rule 14 (Volume Profile Point of Control - POC)
    look_v = min(30, len(df))
    last_30_c = c.iloc[-look_v:]; last_30_v = v_series.iloc[-look_v:]
    bins = np.linspace(last_30_c.min(), last_30_c.max(), 10)
    v_hist, _ = np.histogram(last_30_c, bins=bins, weights=last_30_v)
    poc_level = float((bins[np.argmax(v_hist)] + bins[np.argmax(v_hist)+1])/2)
    near_poc = abs(last - poc_level) < (atr_v * 0.4)

    # Rule 12 (Session Timing Check 1:30 PM IST)
    now_time = datetime.now().time()
    london_active = now_time >= time(13, 30)

    # Core Signals
    choch_bull=last>recent_high; choch_bear=last<recent_low
    prev_o=float(o.iloc[-2]); prev_c=float(c.iloc[-2]); last_o=float(o.iloc[-1])
    bull_eng=(prev_c<prev_o) and (last>last_o) and (last>prev_o) and (last_o<prev_c)
    bear_eng=(prev_c>prev_o) and (last<last_o) and (last<prev_o) and (last_o>prev_c)

    # Liquidity Sweep Engine
    liq_sweep_bull = False; liq_sweep_bear = False
    look_liq = 30
    highs_30 = h.iloc[-look_liq-5:-5]; lows_30 = l.iloc[-look_liq-5:-5]
    tol = atr_v * 0.15
    for i in range(len(highs_30)-1):
        for j in range(i+1, len(highs_30)):
            if abs(float(highs_30.iloc[i]) - float(highs_30.iloc[j])) < tol:
                eqh_level = float(highs_30.iloc[i])
                if h.iloc[-2] > eqh_level and last < eqh_level: liq_sweep_bear = True; break
    for i in range(len(lows_30)-1):
        for j in range(i+1, len(lows_30)):
            if abs(float(lows_30.iloc[i]) - float(lows_30.iloc[j])) < tol:
                eql_level = float(lows_30.iloc[i])
                if l.iloc[-2] < eql_level and last > eql_level: liq_sweep_bull = True; break

    if tf_val == "1m" or tf_val == "5m": lookback_fvg = 100
    elif tf_val == "15m": lookback_fvg = 50
    elif tf_val == "1h": lookback_fvg = 24
    else: lookback_fvg = 10

    bull_fvg=None; bear_fvg=None; bull_fvg_list=[]; bear_fvg_list=[]
    min_fvg_size = atr_v * 0.5
    for i in range(len(df)-lookback_fvg, len(df)-2):
        if i < 1: continue
        if h.iloc[i-1] < l.iloc[i+1] and (l.iloc[i+1] - h.iloc[i-1]) > min_fvg_size:
            fvg_low = float(h.iloc[i-1]); fvg_high = float(l.iloc[i+1])
            fvg_mid = (fvg_low + fvg_high)/2
            if fvg_low <= last <= fvg_high: continue
            mitigated=False
            for j in range(i+2, len(df)-1):
                if l.iloc[j] <= fvg_mid: mitigated=True; break
            if not mitigated: fv=(fvg_low, fvg_high); bull_fvg_list.append(fv); bull_fvg=fv
        if l.iloc[i-1] > h.iloc[i+1] and (l.iloc[i-1] - h.iloc[i+1]) > min_fvg_size:
            fvg_low = float(h.iloc[i+1]); fvg_high = float(l.iloc[i-1])
            fvg_mid = (fvg_low + fvg_high)/2
            if fvg_low <= last <= fvg_high: continue
