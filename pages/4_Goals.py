import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.helpers import load_transactions
from model.predict import get_monthly_summary

st.set_page_config(page_title="Goals · Carbon", page_icon="🎯", layout="wide")
st.title("🎯 Goals & Progress — February 2026")
st.divider()

transactions = load_transactions()
summary      = get_monthly_summary(transactions)
total        = summary['total_co2e']

# ── Goal Setting ─────────────────────────────────────────────────────────
st.subheader("Set your monthly budget")
col_goal, col_hist = st.columns([2, 1])

with col_goal:
    goal_kg = st.slider("Monthly CO₂e budget (kg)", 10, 80,
                        value=st.session_state.get('carbon_goal', 35), step=1,
                        help="Drag to personalise your monthly carbon budget")
    st.session_state['carbon_goal'] = goal_kg

with col_hist:
    st.metric("January 2026",  "26.1 kg", delta="+2.2 kg vs Dec", delta_color="inverse")
    st.metric("December 2025", "23.9 kg", delta="-1.1 kg vs Nov", delta_color="inverse")

st.divider()

# ── Progress ──────────────────────────────────────────────────────────────
days_elapsed, days_total = 19, 28
projected = total / days_elapsed * days_total
pct       = min(total / goal_kg, 1.0)
remaining = max(goal_kg - total, 0)

p1, p2, p3 = st.columns(3)
with p1: st.metric("Used so far",       f"{total} kg",
                    delta=f"{total - goal_kg*(days_elapsed/days_total):.1f} kg vs pace",
                    delta_color="inverse")
with p2: st.metric("Remaining budget",  f"{remaining:.1f} kg")
with p3: st.metric("Month-end projection", f"{projected:.1f} kg",
                    delta="✅ On Track" if projected < goal_kg else "⚠️ Over Goal")

st.progress(pct, text=f"{total} / {goal_kg} kg ({pct*100:.0f}%)")
if pct > 1.0:   st.error(f"🚨 Over goal by {total - goal_kg:.1f} kg")
elif pct > 0.85: st.warning(f"⚠️ Getting close — {remaining:.1f} kg left, {days_total-days_elapsed} days to go")
else:            st.success(f"✅ On track — {remaining:.1f} kg left, {days_total-days_elapsed} days to go")

st.divider()

# ── What-if Simulator ─────────────────────────────────────────────────────
st.subheader("🔮 What-if Simulator")
st.caption("Adjust your habits and see the projected CO₂e saving.")

wc1, wc2 = st.columns(2)
with wc1:
    n_glovo  = st.number_input("Glovo deliveries this month",  0, 20, 4)
    n_uber   = st.number_input("Uber trips this month",        0, 30, 5)
    n_flight = st.number_input("Flights this month",           0,  5, 0)

with wc2:
    s_glovo  = n_glovo  * 5.1  * 0.22
    s_uber   = n_uber   * 3.2  * 0.75
    s_flight = n_flight * 80.0 * 0.85
    total_saving = s_glovo + s_uber + s_flight
    new_total    = max(total - total_saving, 0)

    st.metric("Current total",     f"{total} kg CO₂e")
    st.metric("Potential savings", f"-{total_saving:.1f} kg",
              delta=f"-{total_saving/total*100:.0f}%", delta_color="inverse")
    st.metric("New projected total", f"{new_total:.1f} kg CO₂e")

# Waterfall chart
fig_wf = go.Figure(go.Waterfall(
    orientation="v",
    measure=["absolute", "relative", "relative", "relative", "total"],
    x=["Current", "Pickup over Delivery", "Transit over Rideshare",
       "Train over Flight", "Projected"],
    y=[total, -s_glovo, -s_uber, -s_flight, None],
    connector={"line": {"color": "#374151"}},
    decreasing={"marker": {"color": "#22c55e"}},
    increasing={"marker": {"color": "#ef4444"}},
    totals={"marker": {"color": "#7c3aed"}},
))
fig_wf.update_layout(
    title="CO₂e Savings Waterfall", yaxis_title="kg CO₂e",
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font_color='white'
)
st.plotly_chart(fig_wf, use_container_width=True)

st.divider()

# ── Editable Action Plan (st.data_editor — advanced widget) ──────────────
st.subheader("📋 Your Action Plan")
actions = pd.DataFrame([
    {"Action": "🛵 Pick up next Glovo order",               "Saving": "~0.8 kg", "Difficulty": "Easy",   "Status": "Planned"},
    {"Action": "🚂 Take Renfe instead of next Uber trip",   "Saving": "~1.6 kg", "Difficulty": "Easy",   "Status": "Planned"},
    {"Action": "🛒 Reduce food delivery to once/week",      "Saving": "~3.2 kg", "Difficulty": "Medium", "Status": "Not started"},
    {"Action": "🌿 Plant-based meals 2× per week",          "Saving": "~2.1 kg", "Difficulty": "Medium", "Status": "Not started"},
])
st.data_editor(
    actions,
    column_config={
        "Action":     st.column_config.TextColumn("Action", width="large"),
        "Saving":     st.column_config.TextColumn("Potential Saving"),
        "Difficulty": st.column_config.SelectboxColumn("Difficulty", options=["Easy","Medium","Hard"]),
        "Status":     st.column_config.SelectboxColumn("Status",
                          options=["Not started","Planned","In progress","Done"]),
    },
    use_container_width=True, hide_index=True
)
