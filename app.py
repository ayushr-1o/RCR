import streamlit as st
import pandas as pd
import plotly.express as px
from utils.helpers import load_transactions, CATEGORY_ICONS
from model.predict import get_monthly_summary

st.set_page_config(
    page_title="Carbon Receipt · Revolut",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌱 Carbon Receipt")
    st.caption("Revolut · Personal Carbon View")
    st.divider()
    st.page_link("app.py",                            label="🏠 Home")
    st.page_link("pages/1_Dashboard.py",            label="📊 Dashboard")
    st.page_link("pages/2_Transactions.py",          label="📋 Transactions")
    st.page_link("pages/3_Transaction_Detail.py",    label="🔍 Transaction Detail")
    st.page_link("pages/4_Goals.py",                 label="🎯 Goals & Progress")
    st.divider()
    st.selectbox("📅 Month", ["February 2026", "January 2026", "December 2025"])
    st.caption("⚠️ Estimates are approximate and depend on available data.")

# ── Data ─────────────────────────────────────────────────────────────────────
transactions = load_transactions()
summary      = get_monthly_summary(transactions)

# ── Page Content ─────────────────────────────────────────────────────────────
st.title("🌱 Your Carbon Receipt")
st.markdown("**February 2026** · Overview")
st.divider()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🌍 Total CO₂e", f"{summary['total_co2e']} kg",
              delta="-8% vs last month", delta_color="inverse")
with col2:
    top_cat = summary['by_category'].index[0]
    st.metric("🔥 Top category",
              f"{CATEGORY_ICONS.get(top_cat,'📦')} {top_cat}",
              delta=f"{summary['by_category'].iloc[0]:.1f} kg")
with col3:
    n = len(summary['transactions'])
    st.metric("💳 Transactions", n)
with col4:
    st.metric("📊 Avg per transaction",
              f"{summary['total_co2e']/n:.2f} kg CO₂e")

st.divider()
st.subheader("What's driving your footprint?")

col_chart, col_action = st.columns([2, 1])
with col_chart:
    df_top = summary['by_merchant'].reset_index()
    df_top.columns = ['Merchant', 'CO₂e (kg)']
    fig = px.bar(df_top, x='Merchant', y='CO₂e (kg)',
                 color='CO₂e (kg)', color_continuous_scale='Purples',
                 title='Top 5 Merchants by CO₂e — February 2026')
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)',
                      font_color='white', coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

with col_action:
    st.markdown("### 💡 Next best actions")
    st.info("🛵 **Pick up Glovo orders** → saves ~0.8 kg CO₂e each")
    st.success("🚂 **Renfe over Uber** → saves ~1.6 kg CO₂e per trip")
    st.divider()
    if st.button("📊 Full Dashboard", type="primary", use_container_width=True):
        st.switch_page("pages/1_Dashboard.py")
    if st.button("📋 All Transactions", use_container_width=True):
        st.switch_page("pages/2_Transactions.py")
