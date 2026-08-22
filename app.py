import streamlit as st, yfinance as yf, pandas as pd, plotly.graph_objects as go
import streamlit.components.v1 as components
from pathlib import Path
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Forex V2.0", layout="wide")

# Same CSS as your demo - Black + Yellow
st.markdown("""
<style>
header[data-testid="stHeader"]{background:#1a1a1a}
div[data-testid="stAppViewContainer"]{background:white}
h1,h2,h3{color:black!important}
div[data-testid="stSelectbox"]>div>div{background:#f1f2f6!important;border-radius:10px}
.stButton>button{background:#FFD700!important;color:black!important;font-weight:800!important;border-radius:14px!important;height:58px!important;width:220px!important;border:2px solid #e6c200}
.metric-card{background:black;border:2px solid #FFD700;border-radius:16px;padding:18px 20px;margin-bottom:16px}
.metric-card.label{color:#888;font-size:14px}
.metric-card.value{color:#FFD700;font-size:36px;font-weight:900}
</style>
""", unsafe_allow_html=True)

# Header like screenshot
st.markdown('<div style="background:#1a1a1a;padding:16px 20px;margin:-60px -60px 20px -60px;display:flex;justify-content:space-between;align-items:center"><h2 style="color:white!important;margin:0">Forex V2.0</h2><div style="width:40px;height:40px;background:linear-gradient(45deg,#00f,#f0f);border-radius:50%"></div></div>', unsafe_allow_html=True)

PAIRS_YF = {
 "XAUUSD SPOT GOLD":"XAUUSD=X","XAGUSD SPOT SILVER":"XAGUSD=X",
 "EURUSD":"EURUSD=X","GBPUSD":"GBPUSD=X","USDJPY":"USDJPY=X","AUDUSD":"AUDUSD=X","USDCHF":"USDCHF=X","NZDUSD":"NZDUSD=X",
 "EURJPY":"EURJPY=X","GBPJPY":"GBPJPY=X","EURGBP":"EURGBP=X",
 "BTC-USD":"BTC-USD","ETH-USD":"ETH-USD","SOL-USD":"SOL-USD",
 "US30":"^DJI","NAS100":"^IXIC","SPX500":"^GSPC"
}
PAIRS_TV = {
 "XAUUSD SPOT GOLD":"OANDA:XAUUSD","XAGUSD SPOT SILVER":"OANDA:XAGUSD",
 "EURUSD":"OANDA:EURUSD","GBPUSD":"OANDA:GBPUSD","USDJPY":"OANDA:USDJPY","AUDUSD":"OANDA:AUDUSD","USDCHF":"OANDA:USDCHF","NZDUSD":"OANDA:NZDUSD",
 "EURJPY":"OANDA:EURJPY","GBPJPY":"OANDA:GBPJPY","EURGBP":"OANDA:EURGBP",
 "BTC-USD":"BINANCE:BTCUSD","ETH-USD":"BINANCE:ETHUSD","SOL-USD":"BINANCE:SOLUSD",
 "US30":"FOREXCOM:DJI","NAS100":"NASDAQ:IXIC","SPX500":"FOREXCOM:SPXUSD"
}
TV_MAP={"1m":"1","5m":"5","15m":"15","1h":"60","4h":"240","1d":"D"}

@st.cache_data(ttl=30)
def load_data(ticker, tf):
    per="7d" if tf=="1m" else "60d" if tf in ["5m","15m","1h"] else "1y"
    df=yf.download(ticker,period=per,interval=tf,auto_adjust=True,progress=False)
    if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
    return df.dropna().tail(500) if not df.empty else pd.DataFrame()

DATA_FILE=Path("trading_history.csv")
def save_history(pair,tf,price,buy,sell,sl,tp):
    row={"DateTime":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"Pair":pair,"TF":tf,"Price":price,"BUY%":buy,"SELL%":sell,"SL":sl,"TP":tp}
    df=pd.DataFrame([row])
    if DATA_FILE.exists(): df=pd.concat([pd.read_csv(DATA_FILE),df],ignore_index=True).tail(100)
    df.to_csv(DATA_FILE,index=False)

pair=st.selectbox("Pair Select Karo - 18 Pairs", list(PAIRS_YF.keys()), index=0)
tf=st.selectbox("Timeframe", ("1m","5m","15m","1h","4h","1d"), index=3)

if st.button("START ANALYSIS"):
    df=load_data(PAIRS_YF[pair], tf)
    if df.empty or len(df)<50:
        st.warning("Data load slow hai, 10 sec baad dobara dabao"); st.stop()

    c,h,l,o=df['Close'].astype(float),df['High'].astype(float),df['Low'].astype(float),df['Open'].astype(float)
    ema20=c.ewm(20).mean(); ema50=c.ewm(50).mean(); ema200=c.ewm(200).mean()
    delta=c.diff(); gain=delta.clip(lower=0).ewm(alpha=1/14).mean(); loss=(-delta.clip(upper=0)).ewm(alpha=1/14).mean()
    rsi=100-(100/(1+gain/loss.replace(0,0.001)))
    tr=pd.concat([h-l,(h-c.shift(1)).abs(),(l-c.shift(1)).abs()],axis=1).max(axis=1); atr=tr.ewm(alpha=1/14).mean()

    last=float(c.iloc[-1]); e20=float(ema20.iloc[-1]); e50=float(ema50.iloc[-1]); e200=float(ema200.iloc[-1])
    rsi_v=float(rsi.iloc[-1]); atr_v=float(atr.iloc[-1])
    supp=float(l.iloc[-30:-1].min()); res=float(h.iloc[-30:-1].max())

    # 2. CHoCH / BOS
    recent_high=h.iloc[-15:-2].max(); recent_low=l.iloc[-15:-2].min()
    choch_bull=last>recent_high; choch_bear=last<recent_low
    bos_bull=e20>e50>e200; bos_bear=e20<e50<e200

    # 3. Engulfing Pattern
    prev_o=float(o.iloc[-2]); prev_c=float(c.iloc[-2]); last_o=float(o.iloc[-1])
    bull_eng=(prev_c<prev_o) and (last>last_o) and (last>prev_o) and (last_o<prev_c)
    bear_eng=(prev_c>prev_o) and (last<last_o) and (last<prev_o) and (last_o>prev_c)

    # 4. FVG + OB - SMC NIYAM KE HISAB SE FIX KIYA HAI
    # Timeframe ke hisab se kitna peeche dekhna hai
    if tf == "1m" or tf == "5m": lookback_fvg = 100
    elif tf == "15m": lookback_fvg = 50
    elif tf == "1h": lookback_fvg = 24
    elif tf == "4h": lookback_fvg = 18
    else: lookback_fvg = 10 # 1d

    bull_fvg=None; bear_fvg=None
    bull_fvg_list=[]; bear_fvg_list=[]
    for i in range(len(df)-lookback_fvg, len(df)-1):
        # Gap ATR ka 25% se bada hona chahiye warna kachra gap hai
        if h.iloc[i-1] < l.iloc[i+1] and (l.iloc[i+1] - h.iloc[i-1]) > atr_v*0.25:
            fv=(float(h.iloc[i-1]), float(l.iloc[i+1]))
            bull_fvg_list.append(fv); bull_fvg=fv
        if l.iloc[i-1] > h.iloc[i+1] and (l.iloc[i-1] - h.iloc[i+1]) > atr_v*0.25:
            fv=(float(h.iloc[i+1]), float(l.iloc[i-1]))
            bear_fvg_list.append(fv); bear_fvg=fv

    bull_ob=None; bear_ob=None
    for i in range(len(df)-15,len(df)-2):
        if c.iloc[i]<o.iloc[i] and c.iloc[i+1]>o.iloc[i+1] and c.iloc[i+2]>h.iloc[i]: bull_ob=(float(l.iloc[i]),float(h.iloc[i]))
        if c.iloc[i]>o.iloc[i] and c.iloc[i+1]<o.iloc[i+1] and c.iloc[i+2]<l.iloc[i]: bear_ob=(float(l.iloc[i]),float(h.iloc[i]))

    # Scoring with 2,3,4,5
    score=50; reasons=[]
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
    reasons.append(f"LIVE {last:.5f} = {PAIRS_TV[pair]} {last:.5f}")
    if 45<=rsi_v<=68: reasons.append(f"RSI Neutral {rsi_v:.1f}")
    elif rsi_v>70: reasons.append(f"RSI Overbought {rsi_v:.1f}")
    else: reasons.append(f"RSI Oversold {rsi_v:.1f}")

    buy=max(5,min(95,score)); sell=100-buy
    change=float(c.iloc[-1]-c.iloc[-2])
    sl_long=last-atr_v*1.5; tp1_long=last+atr_v*1.8; tp2_long=last+atr_v*3.0; tp3_long=last+atr_v*5.0
    sl_short=last+atr_v*1.5; tp1_short=last-atr_v*1.8; tp2_short=last-atr_v*3.0

    # Same UI as screenshot
    st.markdown(f'<div class="metric-card"><div class="label">BUY %</div><div class="value">{buy}%</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-card"><div class="label">SELL %</div><div class="value">{sell}%</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-card"><div class="label">LIVE</div><div class="value">{last:.4f}<div style="background:#0a3d1a;color:#00ff66;font-size:14px;padding:4px 10px;border-radius:12px;display:inline-block;margin-top:8px">{"↑" if change>=0 else "↓"} {change:+.5f}</div></div></div>', unsafe_allow_html=True)

    with st.expander("📝 AI THESIS - Reasons", expanded=False):
        for r in reasons: st.write(f"✅ {r}" if "Bullish" in r or "Support" in r else f"🔴 {r}" if "Bearish" in r or "Resistance" in r else f"📊 {r}")

    # Green Box same as screenshot
    if buy>=55:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#002200,#00a300);border:3px solid #00ff66;border-radius:20px;padding:20px;text-align:center;color:white">
        <div style="font-size:28px;font-weight:900">🚀 BUY {pair} @ {last:.5f}</div>
        <div style="display:flex;gap:12px;margin-top:18px">
          <div style="flex:1;background:black;border:2px solid #FFD700;border-radius:14px;padding:12px"><div style="color:#FFD700;font-weight:800">⚡ SHORT</div><div style="font-size:13px;margin-top:6px">SL {sl_short:.5f} ({int(atr_v*100)} pt)<br>TP1 {tp1_short:.5f}<br>TP2 {tp2_short:.5f}</div></div>
          <div style="flex:1;background:black;border:2px solid #00ff66;border-radius:14px;padding:12px"><div style="color:#00ff66;font-weight:800">🚀 LONG</div><div style="font-size:13px;margin-top:6px">SL {sl_long:.5f}<br>TP1 {tp1_long:.5f}<br>TP2 {tp2_long:.5f}<br>TP3 {tp3_long:.5f}</div></div>
        </div></div>
        """, unsafe_allow_html=True)
        save_history(pair,tf,last,buy,sell,sl_long,tp1_long)
    else:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#330000,#cc0000);border:3px solid #ff4444;border-radius:20px;padding:20px;text-align:center;color:white">
        <div style="font-size:28px;font-weight:900">📉 SELL {pair} @ {last:.5f}</div>
        <div style="display:flex;gap:12px;margin-top:18px">
          <div style="flex:1;background:black;border:2px solid #FFD700;border-radius:14px;padding:12px"><div style="color:#FFD700;font-weight:800">⚡ SHORT</div><div style="font-size:13px;margin-top:6px">SL {sl_short:.5f}<br>TP1 {tp1_short:.5f}<br>TP2 {tp2_short:.5f}</div></div>
          <div style="flex:1;background:black;border:2px solid #00ff66;border-radius:14px;padding:12px"><div style="color:#00ff66;font-weight:800">🚀 LONG</div><div style="font-size:13px;margin-top:6px">SL {sl_long:.5f}<br>TP1 {tp1_long:.5f}<br>TP2 {tp2_long:.5f}<br>TP3 {tp3_long:.5f}</div></div>
        </div></div>
        """, unsafe_allow_html=True)
        save_history(pair,tf,last,buy,sell,sl_short,tp1_short)

    st.success(f"✅ Data Save Ho Gaya - {DATA_FILE}")

    if DATA_FILE.exists():
        st.subheader("📁 Last 5 Saved")
        st.dataframe(pd.read_csv(DATA_FILE).tail(5), use_container_width=True)

    st.markdown(f"### 📈 TradingView - {PAIRS_TV[pair]}")
    components.iframe(f"https://s.tradingview.com/widgetembed/?symbol={PAIRS_TV[pair]}&interval={TV_MAP[tf]}&theme=dark&style=1&timezone=Asia/Kolkata", height=550)

    fig=go.Figure(data=[go.Candlestick(x=df.index,open=o,high=h,low=l,close=c)])
    fig.add_hline(y=last,line_color="white",annotation_text=f"LIVE {last:.2f}")
    fig.add_hline(y=sl_long,line_color="red",annotation_text="SL LONG"); fig.add_hline(y=tp1_long,line_color="green",annotation_text="TP1")
    # Sare FVG dikhao chart pe
    for fv in bull_fvg_list[-3:]:
        fig.add_hrect(y0=fv[0], y1=fv[1], fillcolor="green", opacity=0.25, line_width=0, annotation_text="Bull FVG", annotation_position="top left")
    for fv in bear_fvg_list[-3:]:
        fig.add_hrect(y0=fv[0], y1=fv[1], fillcolor="red", opacity=0.25, line_width=0, annotation_text="Bear FVG", annotation_position="bottom left")
    fig.update_layout(template="plotly_dark",height=600,xaxis_rangeslider_visible=False,dragmode='pan',paper_bgcolor='black',plot_bgcolor='black')
    st.plotly_chart(fig,use_container_width=True,config={'scrollZoom':True})
