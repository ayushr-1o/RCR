import streamlit as st
import pandas as pd
from utils.helpers import load_transactions, CATEGORY_ICONS, confidence_dot, confidence_badge_html
from model.predict import get_monthly_summary

st.set_page_config(page_title="Transactions · Carbon", page_icon="📋", layout="wide")
st.title("📋 Transactions — February 2026")
st.divider()

transactions = load_transactions()
summary      = get_monthly_summary(transactions)
df           = summary['transactions'].copy()
df['date']   = pd.to_datetime(df['date'])

# ── Filters ───────────────────────────────────────────────────────────────
with st.expander("🔍 Filter & Sort", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        categories  = ['All'] + sorted(df['category'].unique().tolist())
        sel_cat     = st.selectbox("Category", categories)
    with col2:
        sel_conf    = st.selectbox("Confidence", ['All', 'High', 'Medium', 'Low'])
    with col3:
        sort_by = st.radio("Sort by",
                           ["CO₂e ↓", "Date ↓", "Amount ↓"],
                           horizontal=True)

filtered = df.copy()
if sel_cat  != 'All': filtered = filtered[filtered['category']   == sel_cat]
if sel_conf != 'All': filtered = filtered[filtered['confidence'] == sel_conf]

sort_map = {"CO₂e ↓": 'co2e_kg', "Date ↓": 'date', "Amount ↓": 'amount_eur'}
filtered = filtered.sort_values(sort_map[sort_by], ascending=False)

# ── Toggle: high-impact only ───────────────────────────────────────────────
show_hi = st.toggle("⚡ High impact only (> 3 kg CO₂e)", value=False)
if show_hi:
    filtered = filtered[filtered['co2e_kg'] > 3.0]

st.markdown(
    f"**{len(filtered)} transactions** | "
    f"**{filtered['co2e_kg'].sum():.2f} kg CO₂e** | "
    f"**€{filtered['amount_eur'].sum():.2f}**"
)
st.divider()

# ── Transaction cards ─────────────────────────────────────────────────────
for _, row in filtered.iterrows():
    icon = CATEGORY_ICONS.get(row['category'], '📦')
    with st.container(border=True):
        c1, c2, c3, c4, c5 = st.columns([2, 3, 2, 3, 1])
        with c1:
            st.markdown(f"**{row['date'].strftime('%b %d')}**")
            st.caption(row['category'])
        with c2:
            st.markdown(f"{icon} **{row['merchant']}**")
        with c3:
            st.markdown(f"€ {row['amount_eur']:.2f}")
        with c4:
            st.markdown(f"🌿 **{row['co2e_kg']} kg CO₂e**")
            st.markdown(
                confidence_badge_html(row['confidence']) + " confidence",
                unsafe_allow_html=True
            )
        with c5:
            if st.button("→", key=f"tx_{row['id']}", help="View detail"):
                st.session_state['selected_tx_id'] = int(row['id'])
                st.switch_page("pages/3_Transaction_Detail.py")
