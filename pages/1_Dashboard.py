import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.helpers import load_transactions, CATEGORY_ICONS
from model.predict import get_monthly_summary

st.set_page_config(page_title="Dashboard · Carbon", page_icon="📊", layout="wide")
st.title("📊 Carbon Dashboard — February 2026")
st.divider()

transactions = load_transactions()
summary      = get_monthly_summary(transactions)
df           = summary['transactions'].copy()
df['date']   = pd.to_datetime(df['date'])

tab1, tab2, tab3 = st.tabs(["📈 Overview", "🗂️ By Category", "📅 Timeline"])

# ── Tab 1: Overview ────────────────────────────────────────────────────────
with tab1:
    col_kpi, col_pie = st.columns([1, 2])

    with col_kpi:
        total = summary['total_co2e']
        goal  = st.session_state.get('carbon_goal', 35.0)
        pct   = min(total / goal, 1.0)
        st.markdown(f"### {total} kg CO₂e")
        st.progress(pct, text=f"{pct*100:.0f}% of {goal} kg goal")
        if total < goal:
            st.success(f"✅ On track — {goal-total:.1f} kg remaining")
        else:
            st.error(f"⚠️ Over budget by {total-goal:.1f} kg")

        st.divider()
        st.markdown("**Biggest Drivers**")
        for merchant, val in summary['by_merchant'].items():
            cat  = df[df['merchant'] == merchant]['category'].values
            icon = CATEGORY_ICONS.get(cat[0] if len(cat) else 'Other', '📦')
            st.markdown(f"{icon} **{merchant}** — `{val:.1f} kg`")

    with col_pie:
        cat_df = summary['by_category'].reset_index()
        cat_df.columns = ['Category', 'CO₂e (kg)']
        fig = px.pie(cat_df, values='CO₂e (kg)', names='Category',
                     title='CO₂e by Category',
                     color_discrete_sequence=px.colors.sequential.Purples_r)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)

# ── Tab 2: By Category ─────────────────────────────────────────────────────
with tab2:
    col_a, col_b = st.columns(2)
    cat_df = summary['by_category'].reset_index()
    cat_df.columns = ['Category', 'CO₂e (kg)']

    with col_a:
        fig_bar = px.bar(cat_df, x='CO₂e (kg)', y='Category', orientation='h',
                         color='CO₂e (kg)', color_continuous_scale='Purples',
                         title='CO₂e by Category')
        fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'},
                               paper_bgcolor='rgba(0,0,0,0)',
                               plot_bgcolor='rgba(0,0,0,0)',
                               font_color='white', coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_b:
        st.markdown("### Confidence Breakdown")
        conf_counts = df['confidence'].value_counts()
        fig_conf = px.pie(values=conf_counts.values, names=conf_counts.index,
                          color=conf_counts.index,
                          color_discrete_map={'High':'#22c55e','Medium':'#f59e0b','Low':'#ef4444'},
                          title='Estimate Confidence Distribution')
        fig_conf.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig_conf, use_container_width=True)

        st.dataframe(
            cat_df.style.background_gradient(subset=['CO₂e (kg)'], cmap='Purples'),
            use_container_width=True, hide_index=True
        )

# ── Tab 3: Timeline ────────────────────────────────────────────────────────
with tab3:
    daily = df.groupby('date')['co2e_kg'].sum().reset_index()
    daily['cumulative'] = daily['co2e_kg'].cumsum()
    daily['goal_pace']  = (daily.index + 1) / 28 * 35

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=daily['date'], y=daily['cumulative'],
        mode='lines+markers', name='Cumulative CO₂e',
        line=dict(color='#7c3aed', width=3), marker=dict(size=7)
    ))
    fig_line.add_trace(go.Scatter(
        x=daily['date'], y=daily['goal_pace'],
        mode='lines', name='Goal pace',
        line=dict(color='#22c55e', width=2, dash='dash')
    ))
    fig_line.add_hline(y=35, line_dash='dot', line_color='#ef4444',
                       annotation_text='Monthly Goal: 35 kg')
    fig_line.update_layout(
        title='Cumulative CO₂e — February 2026',
        xaxis_title='Date', yaxis_title='kg CO₂e',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    st.plotly_chart(fig_line, use_container_width=True)

    fig_bar2 = px.bar(daily, x='date', y='co2e_kg', title='Daily CO₂e',
                      color='co2e_kg', color_continuous_scale='RdYlGn_r')
    fig_bar2.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font_color='white', coloraxis_showscale=False)
    st.plotly_chart(fig_bar2, use_container_width=True)
