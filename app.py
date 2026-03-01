import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sqlite3
import calendar

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="369 ELITE V43", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background: #05070a; color: #e6edf3; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Orbitron'; color: #00ffcc; text-align: center; text-shadow: 0 0 20px rgba(0,255,204,0.4); padding: 10px 0; }
    
    /* Metric Dynamic Colors Fix */
    div[data-testid="stMetricDelta"] > div { font-weight: bold !important; }
    div[data-testid="stMetricDelta"] > div[data-direction="down"] { color: #ef4444 !important; } /* الأحمر للخسارة */
    div[data-testid="stMetricDelta"] > div[data-direction="up"] { color: #34d399 !important; }   /* الأخضر للربح */
    
    /* Calendar المستطيلات */
    .cal-card { border-radius: 8px; padding: 10px; text-align: center; min-height: 95px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 10px; transition: 0.3s; }
    .cal-win { background: linear-gradient(135deg, rgba(45, 101, 74, 0.5), rgba(20, 50, 40, 0.7)); border-top: 4px solid #34d399; }
    .cal-loss { background: linear-gradient(135deg, rgba(127, 45, 45, 0.5), rgba(60, 20, 20, 0.7)); border-top: 4px solid #ef4444; }
    .cal-be { background: linear-gradient(135deg, rgba(180, 130, 40, 0.5), rgba(80, 60, 20, 0.7)); border-top: 4px solid #fbbf24; }
    .cal-empty { background: #161b22; opacity: 0.3; }
    .cal-date { font-size: 0.8rem; color: #8b949e; margin-bottom: 5px; }
    .cal-pnl { font-weight: bold; font-size: 0.9rem; color: #fff; }
    .cal-count { font-size: 0.7rem; color: #00ffcc; }

    div[data-testid="stMetric"] { background: rgba(22, 27, 34, 0.7) !important; border: 1px solid #30363d !important; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ---
conn = sqlite3.connect('elite_v43.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS trades 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, pair TEXT, 
              outcome TEXT, pnl REAL, rr REAL, balance REAL, mindset TEXT, setup TEXT)''')
conn.commit()

# --- 3. DATA PREP ---
df = pd.read_sql_query("SELECT * FROM trades", conn)
current_balance = 0.0
daily_net_pnl = 0.0
initial_bal = 1000.0

if not df.empty:
    df['date_dt'] = pd.to_datetime(df['date'])
    # ترتيب حسب التاريخ ثم الـ ID لضمان تسلسل الشارت الحقيقي
    df = df.sort_values(by=['date_dt', 'id']) 
    initial_bal = df['balance'].iloc[0]
    df['cum_pnl'] = df['pnl'].cumsum()
    df['equity_curve'] = initial_bal + df['cum_pnl']
    current_balance = df['equity_curve'].iloc[-1]
    
    # حساب صافي اليوم
    today_str = datetime.now().strftime('%Y-%m-%d')
    daily_net_pnl = df[df['date'] == today_str]['pnl'].sum()

# --- 4. HEADER ---
st.markdown('<h1 class="main-title">369 TRACKER PRO</h1>', unsafe_allow_html=True)
col_eq1, col_eq2, col_eq3 = st.columns([1, 1.5, 1])
with col_eq2:
    st.metric(
        label="CURRENT EQUITY", 
        value=f"${current_balance:,.2f}", 
        delta=f"{daily_net_pnl:+.2f} USD Today", 
        delta_color="normal"
    )

tabs = st.tabs(["🚀 TERMINAL", "📅 CALENDAR LOG", "📊 MONTHLY %", "🧬 ANALYZERS", "📜 JOURNAL"])

# --- TAB 1: TERMINAL (Real-Time Growth Chart) ---
with tabs[0]:
    c1, c2 = st.columns([1, 2.3])
    with c1:
        with st.form("entry_v43", clear_on_submit=True):
            st.markdown("### 📝 Log Trade")
            bal_in = st.number_input("Initial Balance ($)", value=initial_bal)
            d_in = st.date_input("Date", datetime.now())
            asset = st.text_input("Pair", "NAS100").upper()
            res = st.selectbox("Outcome", ["WIN", "LOSS", "BE"])
            p_val = st.number_input("P&L ($)", value=0.0)
            r_val = st.number_input("RR Ratio", value=0.0)
            setup = st.text_input("Setup").upper()
            mind = st.selectbox("Mindset", ["Focused", "Impulsive", "Revenge", "Bored"])
            if st.form_submit_button("LOCK TRADE"):
                c.execute("INSERT INTO trades (date, pair, outcome, pnl, rr, balance, mindset, setup) VALUES (?,?,?,?,?,?,?,?)",
                          (str(d_in), asset, res, p_val, r_val, bal_in, mind, setup))
                conn.commit()
                st.rerun()
    with c2:
        if not df.empty:
            fig_eq = go.Figure()
            # خط الصفر (الرصيد المبدئي)
            fig_eq.add_hline(y=initial_bal, line_dash="dash", line_color="rgba(255,255,255,0.2)")
            # الشارت الحقيقي المتسلسل
            fig_eq.add_trace(go.Scatter(
                x=list(range(len(df))), 
                y=df['equity_curve'],
                mode='lines+markers',
                line=dict(color='#00ffcc', width=3, shape='spline'),
                fill='tonexty', fillcolor='rgba(0,255,204,0.05)',
                marker=dict(size=8, color='#00ffcc', line=dict(width=1, color='#05070a')),
                name="Equity"
            ))
            fig_eq.update_layout(template="plotly_dark", height=450, title="📈 REAL-TIME ACCOUNT GROWTH",
                                xaxis_title="Trade Number", yaxis_title="Balance ($)", margin=dict(l=10,r=10,t=40,b=10))
            st.plotly_chart(fig_eq, use_container_width=True)

# --- TAB 2: CALENDAR LOG (المستطيلات الملونة) ---
with tabs[1]:
    if not df.empty:
        today = datetime.now()
        cal = calendar.monthcalendar(today.year, today.month)
        st.markdown(f"### 📅 {today.strftime('%B %Y')}")
        
        # أيام الأسبوع
        h_cols = st.columns(7)
        for i, day_name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            h_cols[i].markdown(f"<p style='text-align:center; color:#8b949e'>{day_name}</p>", unsafe_allow_html=True)
            
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].markdown('<div class="cal-card cal-empty"></div>', unsafe_allow_html=True)
                else:
                    date_str = datetime(today.year, today.month, day).strftime('%Y-%m-%d')
                    day_df = df[df['date'] == date_str]
                    p_sum = day_df['pnl'].sum()
                    t_count = len(day_df)
                    
                    # تحديد ستايل المستطيل
                    style = "cal-empty"
                    if t_count > 0:
                        style = "cal-win" if p_sum > 0 else "cal-loss" if p_sum < 0 else "cal-be"
                    
                    cols[i].markdown(f"""
                        <div class="cal-card {style}">
                            <div class="cal-date">{day}</div>
                            <div class="cal-pnl">{f"${p_sum:,.2f}" if t_count > 0 else ""}</div>
                            <div class="cal-count">{f"{t_count} Trades" if t_count > 0 else ""}</div>
                        </div>
                    """, unsafe_allow_html=True)

# --- TAB 3: MONTHLY % (Zero-Centered Bar) ---
with tabs[2]:
    if not df.empty:
        df['month'] = df['date_dt'].dt.strftime('%b %Y')
        m_df = df.groupby('month')['pnl'].sum().reset_index()
        fig_m = go.Figure(go.Bar(x=m_df['month'], y=m_df['pnl'], 
                                marker_color=['#34d399' if x > 0 else '#ef4444' for x in m_df['pnl']]))
        fig_m.update_layout(template="plotly_dark", yaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='white', title="P&L ($)"))
        st.plotly_chart(fig_m, use_container_width=True)

# --- TAB 4: ANALYZERS (Mindset, Discipline, Consistency) ---
with tabs[3]:
    if not df.empty:
        st.subheader("🧬 Performance DNA")
        # حساب نقاط الانضباط
        avg_w = df[df['pnl'] > 0]['pnl'].mean() if not df[df['pnl'] > 0].empty else 1
        avg_l = abs(df[df['pnl'] < 0]['pnl'].mean()) if not df[df['pnl'] < 0].empty else 1
        wr = len(df[df['outcome']=='WIN']) / len(df)
        score = min((avg_w / avg_l) * wr * 10, 10.0)
        
        c_m1, c_m2 = st.columns(2)
        with c_m1: 
            st.metric("Consistency Score", f"{score:.1f} / 10")
            st.progress(score/10)
        
        st.divider()
        c_a, c_b = st.columns(2)
        with c_a: 
            st.plotly_chart(px.scatter(df, x='rr', y='pnl', color='outcome', title="Discipline: RR vs Profit", template="plotly_dark"), use_container_width=True)
        with c_b: 
            st.plotly_chart(px.bar(df.groupby('mindset')['pnl'].sum().reset_index(), x='mindset', y='pnl', title="Mindset Analysis", template="plotly_dark"), use_container_width=True)

# --- TAB 5: JOURNAL ---
with tabs[4]:
    if not df.empty:
        st.dataframe(df.sort_values('id', ascending=False), use_container_width=True)
