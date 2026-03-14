import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.helpers import load_transactions, CATEGORY_ICONS
from model.predict import estimate_co2e
from components.gauge import render_co2e_gauge

st.set_page_config(page_title="Detail · Carbon", page_icon="🔍", layout="wide")

transactions = load_transactions()
st.title("🔍 Transaction Detail")

# ── Transaction selector (also receives from session_state) ───────────────
tx_id       = st.session_state.get('selected_tx_id', 3)
tx_labels   = {
    f"{r['merchant']} — €{r['amount_eur']} ({r['date']})": r['id']
    for _, r in transactions.iterrows()
}
ids = list(tx_labels.values())
default_idx = ids.index(tx_id) if tx_id in ids else 0

sel_label   = st.selectbox("Select transaction", list(tx_labels.keys()), index=default_idx)
tx_id       = tx_labels[sel_label]
row         = transactions[transactions['id'] == tx_id].iloc[0]
st.divider()

# ── Delivery mode clarification ───────────────────────────────────────────
delivery_mode = None
if row['category'] == 'Food Delivery':
    st.info("💡 Help improve accuracy: how did you receive this order?")
    delivery_mode = st.radio("Delivery mode", ['Delivery', 'Pickup'],
                             horizontal=True, key='del_mode')

# ── Run prediction ────────────────────────────────────────────────────────
transaction_input = {
    'merchant':      row['merchant'],
    'category':      row['category'],
    'amount_eur':    row['amount_eur'],
    'merchant_known': True
}
result = estimate_co2e(transaction_input, delivery_mode=delivery_mode)

# ── Layout ────────────────────────────────────────────────────────────────
col_main, col_side = st.columns([3, 2])

with col_main:
    icon = CATEGORY_ICONS.get(row['category'], '📦')
    st.markdown(f"## {icon} {row['merchant']} — €{row['amount_eur']:.2f}")
    st.caption(f"📅 {row['date']} · {row['category']}")

    # ── CO₂e estimate card (custom HTML, matches your mockup) ─────────────
    conf_bg = {'High':'#166534','Medium':'#92400e','Low':'#7f1d1d'}.get(
        result['confidence'], '#374151'
    )
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#4c1d95,#6d28d9);
                border-radius:16px;padding:1.5rem;margin:1rem 0">
      <p style="color:#c4b5fd;margin:0;font-size:.9rem">Estimated CO₂e</p>
      <p style="color:white;font-size:2.4rem;font-weight:700;margin:.2rem 0">
         {result['co2e_kg']} kg CO₂e</p>
      <span style="background:{conf_bg};color:white;padding:4px 14px;
                   border-radius:999px;font-size:.85rem;font-weight:700">
        Confidence: {result['confidence']}
      </span>
    </div>
    """, unsafe_allow_html=True)

    # Custom SVG gauge component
    render_co2e_gauge(result['co2e_kg'], max_val=12.0)

    # ── Why this estimate ─────────────────────────────────────────────────
    with st.expander("❓ Why this estimate?"):
        st.markdown(result['explanation'])
        e1, e2 = st.columns(2)
        with e1: st.metric("Emission Factor", f"{result['emission_factor']} kg CO₂e/€")
        with e2: st.metric("Source", result['source'])

    # ── What-if simulator ─────────────────────────────────────────────────
    if result['swap_suggestion']:
        swap = result['swap_suggestion']
        with st.expander("🔄 What-if simulator", expanded=True):
            st.markdown(f"**{swap['tip']}**")
            now_val = result['co2e_kg']
            new_val = round(now_val - swap['saving_kg'], 2)

            m1, m2 = st.columns(2)
            with m1: st.metric("Current CO₂e",               f"{now_val} kg")
            with m2: st.metric(f"If: {swap['swap_to']}",      f"{new_val} kg",
                                delta=f"-{swap['saving_kg']} kg", delta_color="inverse")

            # Plotly gauge
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=now_val,
                delta={'reference': new_val, 'suffix': ' kg', 'valueformat': '.2f'},
                gauge={
                    'axis': {'range': [0, max(now_val * 1.6, 10)]},
                    'bar':  {'color': '#7c3aed'},
                    'steps': [
                        {'range': [0, 2],                         'color': '#166534'},
                        {'range': [2, 5],                         'color': '#92400e'},
                        {'range': [5, max(now_val * 1.6, 10)],    'color': '#7f1d1d'},
                    ],
                    'threshold': {'line': {'color': '#22c55e', 'width': 4},
                                  'thickness': 0.75, 'value': new_val},
                },
                title={'text': 'CO₂e (kg)', 'font': {'color': 'white'}},
                number={'suffix': ' kg', 'font': {'color': 'white'}}
            ))
            fig_g.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                                 font_color='white', height=280)
            st.plotly_chart(fig_g, use_container_width=True)

    # ── AI Carbon Narrative ───────────────────────────────────────────────────
    st.markdown("### 🌿 AI Carbon Insight")
    if st.button("✨ Generate AI narrative", type="primary", use_container_width=True):
        with st.spinner("Generating personalised insight..."):
            try:
                from llm.transaction_narrator import get_transaction_narrative
                nd = get_transaction_narrative(transaction_input, result)
                st.session_state[f"narrative_{tx_id}"] = nd
            except Exception as e:
                st.error(f"Could not generate narrative: {e}")

    if f"narrative_{tx_id}" in st.session_state:
        nd          = st.session_state[f"narrative_{tx_id}"]
        score       = nd.get("eco_score", 5)
        impact      = nd.get("impact_level", "Moderate")
        score_color = "#22c55e" if score >= 7 else "#f59e0b" if score >= 4 else "#ef4444"

        # Eco score card
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0f172a,#1e1b4b);
                    border-radius:16px;padding:1.2rem;margin:.5rem 0;
                    border:1px solid #312e81">
          <div style="display:flex;align-items:center;gap:1rem">
            <div style="background:{score_color};color:white;font-size:1.6rem;
                        font-weight:700;width:58px;height:58px;border-radius:50%;
                        display:flex;align-items:center;justify-content:center">
              {score}
            </div>
            <div>
              <p style="margin:0;font-size:.8rem;color:#9ca3af">Eco Score / 10</p>
              <p style="margin:0;font-size:1.1rem;font-weight:700;color:{score_color}">
                {impact} Impact
              </p>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"**{nd.get('narrative', '')}**")
        st.caption(f"🔍 {nd.get('comparison_context', '')}")

        st.markdown("**💡 Tips for this category:**")
        for tip in nd.get("three_tips", []):
            st.markdown(f"- {tip}")

    # ── Action buttons ────────────────────────────────────────────────────
    st.markdown("### Take action")
    b1, b2 = st.columns(2)
    with b1:
        if st.button("🔔 Remind me next time", use_container_width=True):
            st.toast(f"Reminder set for next {row['category']} order!", icon="🔔")
    with b2:
        if st.button("📅 Add to action plan", use_container_width=True):
            st.toast("Added to your carbon action plan!", icon="📅")

with col_side:
    st.markdown("### 🏷️ Transaction Info")
    info = {
        "Merchant":   row['merchant'],    "Category":   row['category'],
        "Amount":     f"€{row['amount_eur']:.2f}", "Date": str(row['date']),
        "CO₂e":       f"{result['co2e_kg']} kg",   "Confidence": result['confidence'],
        "Source":     result['source'],
    }
    for k, v in info.items():
        st.markdown(f"**{k}:** {v}")

    st.divider()
    st.markdown("### 📊 Benchmark")
    bench = pd.DataFrame({
        'Label':    ['This transaction', 'Category avg', 'Monthly avg / tx'],
        'CO₂e (kg)': [result['co2e_kg'], result['co2e_kg'] * 0.92, 1.2]
    })
    fig_b = px.bar(bench, x='Label', y='CO₂e (kg)', color='CO₂e (kg)',
                   color_continuous_scale='Purples', title='How does it compare?')
    fig_b.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                         plot_bgcolor='rgba(0,0,0,0)',
                         font_color='white', coloraxis_showscale=False)
    st.plotly_chart(fig_b, use_container_width=True)
