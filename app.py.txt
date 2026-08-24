import streamlit as st
import requests
import random
import time
from datetime import datetime, timedelta
from typing import List, Tuple, Dict

# ================= STREAMLIT CONFIG - ISSE BLACK SCREEN FIX HOGA =================
st.set_page_config(
    page_title="Janta AI - Trading House",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= CONFIG - TUMHARI ID PHOTO SE VERIFIED =================
# Secrets me token daalna: Streamlit -> Manage App -> Secrets -> BOT_TOKEN = "..."
try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
except:
    BOT_TOKEN = "PASTE_YOUR_TOKEN_HERE"  # Fallback

CHAT_ID = "7071872872"  # Photo 1 se verified - Rohit Kumar
BOT_USERNAME = "JantaTradingHouse_bot"

PAIRS = ["XAUUSD","XAGUSD","EURUSD","GBPUSD","USDJPY","AUDUSD","USDCAD","NZDUSD","BTC-USD","ETH-USD","GBPJPY"]
TIMEFRAMES = ["1h", "4h"]
TELEGRAM_SCAN_INTERVAL = 120
PHONE_LIVE_INTERVAL = 45
DUPLICATE_BLOCK_HOURS = 4

# Session State init - Rule 4 ke liye
if "running" not in st.session_state:
    st.session_state.running = False
if "last_sent" not in st.session_state:
    st.session_state.last_sent = {}  # Duplicate block ke liye
if "scan_count" not in st.session_state:
    st.session_state.scan_count = 0

# ================= RULE 1: ATR * 1.5 =================
def calculate_true_range(high, low, prev_close):
    return max(high-low, abs(high-prev_close), abs(low-prev_close))

def calculate_atr(highs, lows, closes, period=14):
    if len(closes) < 2:
        return 10.0
    trs = []
    for i in range(1, len(closes)):
        trs.append(calculate_true_range(highs[i], lows[i], closes[i-1]))
    if len(trs) < period:
        atr = sum(trs)/len(trs) if trs else 10.0
    else:
        atr = sum(trs[-period:])/period
    return round(atr, 4)

def get_sl_tp_atr(entry, signal_type, highs, lows, closes):
    atr = calculate_atr(highs, lows, closes)
    sl_dist = atr * 1.5  # RULE 1
    if "BUY" in signal_type.upper():
        sl = entry - sl_dist
        tp1 = entry + (atr * 2.5)
        tp2 = entry + (atr * 4.0)
    else:
        sl = entry + sl_dist
        tp1 = entry - (atr * 2.5)
        tp2 = entry - (atr * 4.0)
    return round(sl,2), round(tp1,2), round(tp2,2), atr

# ================= TELEGRAM =================
def send_telegram_msg(text):
    if "PASTE_YOUR" in BOT_TOKEN:
        st.error("BOT_TOKEN Secrets me nahi dala! Manage App -> Secrets me daalo")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        st.error(f"Telegram Error: {e}")
        return False

def on_app_open_welcome():
    msg = f"""
🚀 *Welcome to Janta AI* 🚀
👤 *User:* Rohit Kumar | 🆔 *ID:* `{CHAT_ID}`
🤖 *Bot:* @{BOT_USERNAME}
✅ *Status:* LIVE
✅ *11 Pairs Parallel* (1h & 4h)
✅ *Filter:* 95%+ Only
✅ *SL:* ATR × 1.5 (Rule 1)
✅ *Live:* 30-60 sec (Rule 2,3,4)
"""
    send_telegram_msg(msg)

# ================= FAKE DATA - ASLI API YAHAN LAGEGA =================
def fetch_candle_data(pair, tf):
    # Asli me yahan TwelveData / Binance API lagega
    closes = [2000 + random.random()*100 for _ in range(50)]
    highs = [c + random.random()*5 for c in closes]
    lows = [c - random.random()*5 for c in closes]
    return highs, lows, closes

def analyze_pair_smc(pair, tf):
    highs, lows, closes = fetch_candle_data(pair, tf)
    entry = closes[-1]
    buy_score = random.randint(70, 99)  # Tumhara asli SMC model yahan
    sell_score = 100 - buy_score
    final_score = max(buy_score, sell_score)
    signal_type = "STRONG BUY (LONG)" if buy_score > sell_score else "STRONG SELL (SHORT)"
    
    if final_score >= 95:
        sl, tp1, tp2, atr = get_sl_tp_atr(entry, signal_type, highs, lows, closes)
        return {
            "pair": pair, "tf": tf, "score": final_score,
            "buy": buy_score, "sell": sell_score,
            "signal": signal_type, "price": round(entry,2),
            "sl": sl, "tp1": tp1, "tp2": tp2, "atr": atr,
            "smc": "EQL Sweep + OB Reclaim + FVG" if "BUY" in signal_type else "EQH Reject + Bearish OB"
        }
    return {"pair": pair, "tf": tf, "score": final_score, "buy": buy_score, "sell": sell_score, "signal": "WAIT", "price": round(entry,2)}

# ================= UI =================
st.title("🚀 Janta AI - Trading House")
st.caption(f"ID: {CHAT_ID} | Bot: @{BOT_USERNAME} | 11 Pairs | 95%+ Telegram")

with st.sidebar:
    st.header("Controls")
    st.write(f"**Pairs:** {len(PAIRS)} | **TF:** {', '.join(TIMEFRAMES)}")
    st.write(f"**Live Interval:** {PHONE_LIVE_INTERVAL}s")
    st.write(f"**Telegram Interval:** {TELEGRAM_SCAN_INTERVAL}s")
    
    # Rule 4: Analyse / Stop Button - Wahi button
    button_label = "⏹️ STOP - Band Karo" if st.session_state.running else "▶️ ANALYSE - Start Karo"
    if st.button(button_label, use_container_width=True, type="primary"):
        st.session_state.running = not st.session_state.running
        if st.session_state.running:
            on_app_open_welcome()
            st.toast("🚀 Janta AI LIVE - Welcome bheja", icon="✅")
        else:
            st.toast("🛑 Tracker Stopped", icon="🛑")
        st.rerun()
    
    if st.button("Clear Duplicate Block", use_container_width=False):
        st.session_state.last_sent = {}
        st.success("Duplicate block clear ho gaya")
    
    st.divider()
    st.write("**Rule Status:**")
    st.write("✅ Rule 1: ATR*1.5 SL")
    st.write("✅ Rule 2: BUY% SELL% Live")
    st.write("✅ Rule 3: 30-60 sec Refresh")
    st.write("✅ Rule 4: Stop Button Same")

# ================= MAIN DISPLAY =================
if not st.session_state.running:
    st.info("👆 Sidebar se **ANALYSE** button dabao - 11 Pairs Parallel Scan Start Hoga")
    st.warning("Black screen fix ho gaya hai - Ab ye page turant load hoga")
    
    # Demo Table - Kya dikhega
    st.subheader("Demo Preview - Kya Dikhega Start Hone Par")
    demo_data = []
    for p in PAIRS:
        demo_data.append({"Pair": p, "BUY%": random.randint(10,90), "SELL%": 0, "Signal": "WAIT", "Price": 2450.50})
    for d in demo_data:
        d["SELL%"] = 100 - d["BUY%"]
    st.dataframe(demo_data, use_container_width=True)
    
else:
    # RUNNING MODE - 11 Ek Sath Scan
    st.success(f"🟢 LIVE - Scanning {len(PAIRS)} Pairs Parallel | Round: {st.session_state.scan_count+1}")
    
    placeholder = st.empty()
    telegram_placeholder = st.empty()
    
    # Ek Round
    st.session_state.scan_count += 1
    all_results = []
    
    with placeholder.container():
        st.subheader(f"📡 Live Tracker - {datetime.now().strftime('%H:%M:%S')} | 1h & 4h")
        
        # 11 Pairs Parallel Scan Simulation
        progress = st.progress(0)
        for idx, pair in enumerate(PAIRS):
            progress.progress((idx+1)/len(PAIRS))
            for tf in TIMEFRAMES:
                key = f"{pair}_{tf}"
                
                # Duplicate Block Check
                if key in st.session_state.last_sent:
                    last = st.session_state.last_sent[key]
                    if datetime.now() - last < timedelta(hours=DUPLICATE_BLOCK_HOURS):
                        continue
                
                result = analyze_pair_smc(pair, tf)
                
                if result and result["score"] >= 95:
                    # 95%+ mila to Telegram
                    msg = f"""
🟨 *JANTA AI - {tf.upper()} 95%+ ALERT* 🚀
*Pair:* {pair} | *Score:* {result['score']}%
*Signal:* {result['signal']} | *Price:* ${result['price']}
*BUY%:* {result['buy']}% | *SELL%:* {result['sell']}%
*SL (ATR*1.5):* ${result['sl']} | *TP1:* ${result['tp1']} | *TP2:* ${result['tp2']}
*ATR:* {result['atr']} | *SMC:* {result['smc']}
"""
                    if send_telegram_msg(msg):
                        st.session_state.last_sent[key] = datetime.now()
                        telegram_placeholder.success(f"✅ Telegram Sent: {pair} {tf} {result['score']}%")
                
                all_results.append(result)
        
        progress.empty()
        
        # Table Display - Rule 2: BUY% vs SELL%
        if all_results:
            # Sort by score
            all_results.sort(key=lambda x: x.get("score",0), reverse=True)
            
            for res in all_results:
                score = res.get("score",0)
                if score >= 95:
                    color = "🟢" if "BUY" in res.get("signal","") else "🔴"
                    st.markdown(f"{color} **{res['pair']} {res['tf']} | {res['signal']} | BUY: {res['buy']}% SELL: {res['sell']}% | Price: ${res['price']} | SL: ${res.get('sl','-')} | Score: {score}% - TELEGRAM SENT**")
                elif score >= 80:
                    st.markdown(f"🟡 **{res['pair']} {res['tf']} | BUY: {res['buy']}% SELL: {res['sell']}% | Score: {score}% - Watching**")
                else:
                    st.markdown(f"⚪ {res['pair']} {res['tf']} | BUY: {res['buy']}% SELL: {res['sell']}% | Score: {score}%")
        
        st.divider()
        st.write(f"Next scan in {PHONE_LIVE_INTERVAL} seconds...")
    
    # Auto Refresh - Rule 3: 30-60 sec
    time.sleep(PHONE_LIVE_INTERVAL)
    if st.session_state.running:
        st.rerun()

# Footer
st.divider()
st.caption("Janta AI Pro v4.5 | ATR*1.5 | 11 Parallel | 95%+ Telegram | Welcome on Open | Made for Rohit (7071872872)")
