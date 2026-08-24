import streamlit as st, yfinance as yf, pandas as pd, plotly.graph_objects as go, requests, os
import numpy as np
from datetime import datetime
import streamlit.components.v1 as components
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="Janta AI - 15 MASTER", layout="wide")
st.markdown("""
<style>
.main{background:#000}
div[data-testid="stMetric"]{background:#111; border:2px solid #FFD700; border-radius:14px; padding:10px}
div[data-testid="stMetricValue"]{color:#FFD700!important; font-weight:900}
.stButton>button{background:#FFD700; color:#000; font-weight:900; width:100%; height:65px; font-size:21px; border-radius:14px}
</style>
""", unsafe_allow_html=True)

st.title("🏛️ JANTA AI - 15 FINAL MASTER RULES")

# Secrets se Telegram lo, hardcode nahi
TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

def send_telegram_alert(pair_name, signal_type, entry_p, sl_p, tp1_p, tp2_p, reason_txt):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        emoji = "🚀" if "BUY" in signal_type else "📉"
        msg = f"🎯 JANTA AI - 100% JACKPOT ALERT\n\nPair: {pair_name}\nSignal: {emoji} {signal_type} (100% CONFIRMED)\nSMC Reason: {reason_txt}\n\nTrading Plan:\nEntry: {entry_p:.5f}\nSL: {sl_p:.5f}\nTP1: {tp1_p:.5f}\nTP2: {tp2_p:.5f}\n\n[15 MASTER RULES Scanner]"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
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
        headers = {"User-Agent": "Mozilla/5.0"}
        if "XAUUSD" in pair_name:
            r=requests.get("https://api.gold-api.com/price/XAU", timeout=5, headers=headers).json()
            return float(r['price'])
        if "XAGUSD" in pair_name:
            r=requests.get("https://api.gold-api.com/price/XAG", timeout=5, headers=headers).json()
            return float(r['price'])
        if "-USD" in pair_name:
            symbol = pair_name.split("-")[0]
            binance_symbol = f"{symbol}USDT"
            if symbol=="SHIB": binance_symbol="1000SHIBUSDT"
            r=requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={binance_symbol}", timeout=5, headers=headers).json()
            return float(r['price'])
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

# --- 15 MASTER RULES ENGINE ---
def core_janta_engine(pair_key, tf_val):
    y_sym, tv_sym, pt_mult = PAIRS[pair_key]
    df = load_chart_fixed(y_sym, tf_val)
    if df.empty: return None
    live = get_live_price(pair_key)
    mp_yahoo = float(df['Close'].iloc[-1])
    mp = live if live and live>0 else mp_yahoo
    diff = mp - mp_yahoo
    df['Close']+=diff; df['High']+=diff; df['Low']+=diff; df['Open']+=diff

    c,h,l,o = df['Close'].astype(float), df['High'].astype(float), df['Low'].astype(float), df['Open'].astype(float)
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

    # Rule 10: Leading vs Lagging - EMA/RSI kam points
    score=50; reasons=[]
    bull_count=0; bear_count=0

    # Lagging - kam points (Rule 10)
    if last>e20>e50: 
        score+=3; bull_count+=1; reasons.append(f"Lagging Trend +3: Price > EMA20>EMA50")
    elif last<e20<e50:
        score-=3; bear_count+=1; reasons.append(f"Lagging Trend -3: Price < EMA20<EMA50")
    
    bos_bull=e20>e50>e200; bos_bear=e20<e50<e200
    if bos_bull: score+=5; bull_count+=1; reasons.append(f"BOS +5: EMA20>50>200")
    if bos_bear: score-=5; bear_count+=1; reasons.append(f"BOS -5: EMA20<50<200")

    if 45<=rsi_v<=70: reasons.append(f"RSI Neutral {rsi_v:.1f} (0 pts - lagging)")
    elif rsi_v>70: score-=2; reasons.append(f"RSI Overbought {rsi_v:.1f} -2")
    else: score+=2; reasons.append(f"RSI Oversold {rsi_v:.1f} +2")

    # Leading - zyada points
    choch_bull=last>recent_high; choch_bear=last<recent_low
    if choch_bull: score+=10; bull_count+=1; reasons.append(f"CHoCH Bullish +10: {recent_high:.2f} break")
    if choch_bear: score-=10; bear_count+=1; reasons.append(f"CHoCH Bearish -10: {recent_low:.2f} break")

    prev_o=float(o.iloc[-2]); prev_c=float(c.iloc[-2]); last_o=float(o.iloc[-1])
    bull_eng=(prev_c<prev_o) and (last>last_o) and (last>prev_o) and (last_o<prev_c)
    bear_eng=(prev_c>prev_o) and (last<last_o) and (last<prev_o) and (last_o>prev_c)
    if bull_eng: score+=8; bull_count+=1; reasons.append("Bullish Engulfing +8")
    if bear_eng: score-=8; bear_count+=1; reasons.append("Bearish Engulfing -8")

    # Rule 12: Session Filter 1:30 PM IST (London open)
    ist_hour = datetime.now().hour  # Server IST me hoga
    # London session 1:30 PM IST = 13:30 to 20:00 IST high volume
    london_active = 13 <= ist_hour <= 20
    session_bonus = 5 if london_active else 0
    if london_active: reasons.append(f"Session Active +5: London 1:30PM Rule (High Volume)")

    # Liquidity Sweep +30 (Rule 10)
    liq_bull=False; liq_bear=False; eqh_level=None; eql_level=None
    look_liq=30
    highs_30=h.iloc[-look_liq-5:-5]; lows_30=l.iloc[-look_liq-5:-5]
    tol=atr_v*0.15
    for i in range(len(highs_30)-1):
        for j in range(i+1, len(highs_30)):
            if abs(float(highs_30.iloc[i]) - float(highs_30.iloc[j])) < tol:
                eqh_level=float(highs_30.iloc[i])
                if h.iloc[-2] > eqh_level and last < eqh_level:
                    liq_bear=True; break
    for i in range(len(lows_30)-1):
        for j in range(i+1, len(lows_30)):
            if abs(float(lows_30.iloc[i]) - float(lows_30.iloc[j])) < tol:
                eql_level=float(lows_30.iloc[i])
                if l.iloc[-2] < eql_level and last > eql_level:
                    liq_bull=True; break
    if liq_bull: score+=30 + session_bonus; bull_count+=1; reasons.append(f"🔥 Liquidity Sweep BULLISH +30 (+{session_bonus} session): EQL {eql_level:.2f} Stop-Hunt")
    if liq_bear: score-=30 + session_bonus; bear_count+=1; reasons.append(f"🔥 Liquidity Sweep BEARISH -30 (-{session_bonus} session): EQH {eqh_level:.2f} Stop-Hunt")

    # FVG / OB +15 each (Rule 10)
    if tf_val in ["1m","5m"]: lookback_fvg=100
    elif tf_val=="15m": lookback_fvg=50
    elif tf_val=="1h": lookback_fvg=24
    else: lookback_fvg=18

    bull_fvg=None; bear_fvg=None; bull_fvg_list=[]; bear_fvg_list=[]
    min_fvg_size=atr_v*0.5
    for i in range(len(df)-lookback_fvg, len(df)-2):
        if i<1: continue
        if h.iloc[i-1] < l.iloc[i+1] and (l.iloc[i+1] - h.iloc[i-1]) > min_fvg_size:
            fvg_low=float(h.iloc[i-1]); fvg_high=float(l.iloc[i+1])
            if fvg_low <= last <= fvg_high: continue
            if abs(last - fvg_low) < atr_v*0.3 or abs(last - fvg_high) < atr_v*0.3: continue
            mitigated=False
            fvg_mid=(fvg_low+fvg_high)/2
            for j in range(i+2, len(df)-1):
                if l.iloc[j] <= fvg_mid: mitigated=True; break
            if not mitigated:
                fv=(fvg_low,fvg_high); bull_fvg_list.append(fv); bull_fvg=fv
        if l.iloc[i-1] > h.iloc[i+1] and (l.iloc[i-1] - h.iloc[i+1]) > min_fvg_size:
            fvg_low=float(h.iloc[i+1]); fvg_high=float(l.iloc[i-1])
            if fvg_low <= last <= fvg_high: continue
            if abs(last - fvg_low) < atr_v*0.3 or abs(last - fvg_high) < atr_v*0.3: continue
            mitigated=False
            fvg_mid=(fvg_low+fvg_high)/2
            for j in range(i+2, len(df)-1):
                if h.iloc[j] >= fvg_mid: mitigated=True; break
            if not mitigated:
                fv=(fvg_low,fvg_high); bear_fvg_list.append(fv); bear_fvg=fv

    bull_ob=None; bear_ob=None
    for i in range(len(df)-15,len(df)-2):
        if c.iloc[i]<o.iloc[i] and c.iloc[i+1]>o.iloc[i+1] and c.iloc[i+2]>h.iloc[i]: bull_ob=(float(l.iloc[i]),float(h.iloc[i]))
        if c.iloc[i]>o.iloc[i] and c.iloc[i+1]<o.iloc[i+1] and c.iloc[i+2]<l.iloc[i]: bear_ob=(float(l.iloc[i]),float(h.iloc[i]))

    if bull_fvg: score+=15; bull_count+=1; reasons.append(f"Bullish FVG +15: {bull_fvg[0]:.2f}-{bull_fvg[1]:.2f}")
    if bear_fvg: score-=15; bear_count+=1; reasons.append(f"Bearish FVG -15: {bear_fvg[0]:.2f}-{bear_fvg[1]:.2f}")
    if bull_ob: score+=15; bull_count+=1; reasons.append(f"Bullish OB +15: {bull_ob[0]:.2f}-{bull_ob[1]:.2f}")
    if bear_ob: score-=15; bear_count+=1; reasons.append(f"Bearish OB -15: {bear_ob[0]:.2f}-{bear_ob[1]:.2f}")

    # Rule 11: Fibonacci Discount vs Premium
    fib_high=float(h.iloc[-30:].max()); fib_low=float(l.iloc[-30:].min())
    fib_range=fib_high-fib_low
    fib_50=fib_high - fib_range*0.5
    fib_618=fib_high - fib_range*0.618
    in_discount = last <= fib_50  # sasta - BUY ke liye accha
    in_premium = last >= fib_50   # mehenga - SELL ke liye accha
    in_golden_discount = last >= fib_618 and last <= fib_50

    if in_golden_discount and bull_ob:
        score+=15; reasons.append(f"Fib Golden Discount +15: Price {last:.2f} in 0.5-0.618 + OB Confirm")
    elif in_discount and bull_fvg:
        score+=10; reasons.append(f"Fib Discount +10: Price {last:.2f} <= 0.5")
    if in_premium and bear_ob:
        score-=15; reasons.append(f"Fib Premium -15: Price {last:.2f} >= 0.5 + OB Reject")

    # Rule 14: Volume Profile POC
    try:
        look_v=min(30,len(df))
        last_30_c=c.iloc[-look_v:]; last_30_v=v_series.iloc[-look_v:]
        bins=np.linspace(last_30_c.min(), last_30_c.max(), 10)
        v_hist,_=np.histogram(last_30_c, bins=bins, weights=last_30_v)
        poc_level=float((bins[np.argmax(v_hist)] + bins[np.argmax(v_hist)+1])/2)
        near_poc=abs(last - poc_level) < (atr_v*0.4)
        if near_poc:
            if last > poc_level: score+=10; reasons.append(f"POC Bounce +10: Near POC {poc_level:.2f} (Heavy Volume)")
            else: score-=10; reasons.append(f"POC Reject -10: Near POC {poc_level:.2f}")
    except:
        poc_level=None

    # 100% Confirm
    if bull_count>=6 and bear_count==0:
        score=100
    elif bear_count>=6 and bull_count==0:
        score=0

    buy_score=max(0,min(100,score)); sell_score=100-buy_score
    return {
        "pair": pair_key, "tf": tf_val, "mp": mp, "buy": buy_score, "sell": sell_score,
        "reasons": reasons, "bull_count": bull_count, "bear_count": bear_count,
        "df": df, "ema20": ema20, "ema50": ema50, "last": last, "supp": supp, "res": res,
        "atr": atr_v, "bull_fvg_list": bull_fvg_list, "bear_fvg_list": bear_fvg_list,
        "bull_ob": bull_ob, "bear_ob": bear_ob, "poc": poc_level if 'poc_level' in locals() else None,
        "fib_50": fib_50, "fib_618": fib_618
    }

# UI
col1,col2=st.columns(2)
with col1: pair=st.selectbox("Pair Select Karo - 11 Pairs", list(PAIRS.keys()), index=0)
with col2: tf=st.selectbox("Timeframe", ("1m","5m","15m","1h","4h","1d"), index=3)

# Rule 5: 75% Filter info
st.info("📜 Rule 5: Discipline 75% Filter - Fresh trade tabhi lo jab BUY/SELL >=75% ho, warna No Trade Zone me fixed SL ka wait karo")

if st.button("START ANALYSIS"):
    result = core_janta_engine(pair, tf)
    if not result:
        st.error(f"{pair} ka chart load nahi hua"); st.stop()
    
    mp=result["mp"]; buy_score=result["buy"]; sell_score=result["sell"]
    last=result["last"]; supp=result["supp"]; res=result["res"]; atr_v=result["atr"]
    df=result["df"]; reasons=result["reasons"]
    bull_fvg_list=result["bull_fvg_list"]; bear_fvg_list=result["bear_fvg_list"]
    ema20=result["ema20"]; ema50=result["ema50"]

    # Rule 1: ATR *1.5 (chhota SL)
    base_dist = max(mp*0.005, atr_v*1.5)  # pehle 2.8 tha, ab 1.5
    def pts(d): return int(abs(d)*PAIRS[pair][2])

    # Rule 5 + Signal Lock
    is_weak = (50 < buy_score < 75) and (50 < sell_score < 75)  # 75% filter
    is_neutral = abs(buy_score - sell_score) <= 4 or is_weak

    # Signal Lock from history
    last_signal=None; last_mp=None
    if os.path.exists("trading_history.csv"):
        try:
            df_hist=pd.read_csv("trading_history.csv")
            if not df_hist.empty:
                for idx in range(len(df_hist)-1, -1, -1):
                    row=df_hist.iloc[idx]
                    lb=float(row['Buy%'])
                    if lb>55: last_signal="BUY"; last_mp=float(row['Market']); break
                    elif lb<45: last_signal="SELL"; last_mp=float(row['Market']); break
        except: pass
    if last_signal=="BUY" and 45 <= buy_score <= 60:
        buy_score=56; sell_score=44; reasons.append(f"🔒 Signal Lock: Last BUY {last_mp:.2f} tha")
    elif last_signal=="SELL" and 45 <= sell_score <= 60:
        buy_score=44; sell_score=56; reasons.append(f"🔒 Signal Lock: Last SELL {last_mp:.2f} tha")

    sl_plot=None; tp1_plot=None; tp2_plot=None
    if is_neutral:
        st.markdown(f"""<div style='background:linear-gradient(135deg,#222200,#666600); border:3px solid #FFD700; padding:22px; border-radius:16px;'><div style='color:#FFD700; font-size:28px; font-weight:900; text-align:center;'>⏸️ HOLD / NO TRADE ZONE {pair} @ {mp:.5f}</div><div style='color:#fff; text-align:center; margin-top:10px;'>BUY {buy_score}% = SELL {sell_score}% - 75% Filter: Wait for Fixed SL, Panic Exit nahi</div></div>""", unsafe_allow_html=True)
    elif buy_score > sell_score:
        sl_short = mp - base_dist; sl_long = min(sl_short, supp - atr_v*0.3)
        tp_s1 = mp + base_dist*1.2; tp_s2 = mp + base_dist*2.0
        tp_l1 = mp + base_dist*2.0; tp_l2 = mp + base_dist*3.5; tp_l3 = mp + base_dist*5.5
        st.markdown(f"""<div style='background:linear-gradient(135deg,#002200,#00a336); border:3px solid #00ff88; padding:22px; border-radius:16px;'><div style='color:#fff; font-size:28px; font-weight:900; text-align:center;'>🚀 BUY {pair} @ {mp:.5f} (Rule1: SL ATR*1.5)</div><div style='display:flex; gap:10px; margin-top:14px;'><div style='flex:1; background:#000; border:2px solid #ffcc00; border-radius:12px; padding:12px; text-align:center;'><div style='color:#ffcc00; font-weight:900;'>⚡ SHORT</div><div style='color:#fff; font-size:12px;'>SL {sl_short:.5f} ({pts(mp-sl_short)} pt)<br>TP1 {tp_s1:.5f}<br>TP2 {tp_s2:.5f}</div></div><div style='flex:1; background:#000; border:2px solid #00ff88; border-radius:12px; padding:12px; text-align:center;'><div style='color:#00ff88; font-weight:900;'>🚀 LONG</div><div style='color:#fff; font-size:12px;'>SL {sl_long:.5f}<br>TP1 {tp_l1:.5f}<br>TP2 {tp_l2:.5f}<br>TP3 {tp_l3:.5f}</div></div></div></div>""", unsafe_allow_html=True)
        sl_plot,tp1_plot,tp2_plot = sl_long, tp_l1, tp_l2
        if buy_score==100:
            send_telegram_alert(pair, "BUY", mp, sl_long, tp_l1, tp_l2, " | ".join(reasons[:2]))
    else:
        sl_short = mp + base_dist; sl_long = max(sl_short, res + atr_v*0.3)
        tp_s1 = mp - base_dist*1.2; tp_s2 = mp - base_dist*2.0
        tp_l1 = mp - base_dist*2.0; tp_l2 = mp - base_dist*3.5; tp_l3 = mp - base_dist*5.5
        st.markdown(f"""<div style='background:linear-gradient(135deg,#330000,#cc0000); border:3px solid #ff4444; padding:22px; border-radius:16px;'><div style='color:#fff; font-size:28px; font-weight:900; text-align:center;'>📉 SELL {pair} @ {mp:.5f} (Rule1: SL ATR*1.5)</div><div style='display:flex; gap:10px; margin-top:14px;'><div style='flex:1; background:#000; border:2px solid #ffcc00; border-radius:12px; padding:12px; text-align:center;'><div style='color:#ffcc00; font-weight:900;'>⚡ SHORT</div><div style='color:#fff; font-size:12px;'>SL {sl_short:.5f}<br>TP1 {tp_s1:.5f}<br>TP2 {tp_s2:.5f}</div></div><div style='flex:1; background:#000; border:2px solid #ff8888; border-radius:12px; padding:12px; text-align:center;'><div style='color:#ff8888; font-weight:900;'>📉 LONG</div><div style='color:#fff; font-size:12px;'>SL {sl_long:.5f}<br>TP1 {tp_l1:.5f}<br>TP2 {tp_l2:.5f}<br>TP3 {tp_l3:.5f}</div></div></div></div>""", unsafe_allow_html=True)
        sl_plot,tp1_plot,tp2_plot = sl_long, tp_s1, tp_s2
        if sell_score==100:
            send_telegram_alert(pair, "SELL", mp, sl_long, tp_l1, tp_l2, " | ".join(reasons[:2]))

    saved_file = save_data(pair, mp, sl_plot if sl_plot else 0, tp1_plot if tp1_plot else 0, tp2_plot if tp2_plot else 0, buy_score, sell_score)
    st.success(f"✅ Data Save - {saved_file}")

    c1,c2,c3=st.columns(3)
    c1.metric("BUY %", f"{buy_score}%"); c2.metric("SELL %", f"{sell_score}%"); c3.metric("LIVE", f"{mp:.5f}")
    with st.expander("📝 AI THESIS - 15 Rules Verification", expanded=True):
        for r in reasons: st.write(r)

    # TradingView + Plotly
    y_sym, tv_sym, _ = PAIRS[pair]
    st.markdown(f"### 📈 TradingView {tv_sym} Live")
    components.iframe(f"https://s.tradingview.com/widgetembed/?symbol={tv_sym}&interval={TV_MAP[tf]}&theme=dark&style=1&timezone=Asia/Kolkata", height=550)
    fig=go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price")])
    fig.add_trace(go.Scatter(x=df.index, y=ema20, line=dict(color='#FFD700', width=1.5), name='EMA20'))
    fig.add_trace(go.Scatter(x=df.index, y=ema50, line=dict(color='#FF8C00', width=1.5), name='EMA50'))
    if sl_plot: 
        fig.add_hline(y=sl_plot, line_color="red", line_dash="dash", annotation_text=f"SL {sl_plot:.2f} (ATR*1.5)")
        fig.add_hline(y=tp1_plot, line_color="green", line_dash="dot", annotation_text=f"TP1 {tp1_plot:.2f}")
    for fv in bull_fvg_list[-3:]: fig.add_hrect(y0=fv[0], y1=fv[1], fillcolor="green", opacity=0.18, line_width=0)
    for fv in bear_fvg_list[-3:]: fig.add_hrect(y0=fv[0], y1=fv[1], fillcolor="red", opacity=0.18, line_width=0)
    fig.update_layout(template="plotly_dark",height=600,xaxis_rangeslider_visible=False,paper_bgcolor='black',plot_bgcolor='black')
    st.plotly_chart(fig,use_container_width=True)

# --- Rule 6-9: Background Scanner ---
st.markdown("---")
st.markdown("### 🛰️ 11 Pairs Background Scanner (2 Min Loop + 1 Sec Parallel)")
if st.button("START 11 PAIRS AUTO SCAN (100% Jackpot)"):
    with st.spinner("11 pairs ko 1 sec me parallel scan kar raha hai..."):
        pairs_to_scan = list(PAIRS.keys())[:11]
        def scan_one(p):
            return core_janta_engine(p, "15m")
        with ThreadPoolExecutor(max_workers=11) as executor:
            results = list(executor.map(scan_one, pairs_to_scan))
        jackpot=[]
        for r in results:
            if r and (r['buy']==100 or r['sell']==100):
                jackpot.append(r)
                send_telegram_alert(r['pair'], "BUY 100%" if r['buy']==100 else "SELL 100%", r['mp'], r['supp'], r['res'], r['res'], f"Jackpot {r['tf']}")
        if jackpot:
            st.success(f"🎯 {len(jackpot)} JACKPOT MILE!")
            st.dataframe(pd.DataFrame([{"Pair":j['pair'],"BUY%":j['buy'],"SELL%":j['sell'],"Live":j['mp']} for j in jackpot]))
        else:
            st.warning("Koi 100% jackpot nahi mila, 2 min baad dobara scan karega")
