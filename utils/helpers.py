import os
import pandas as pd
import streamlit as st

@st.cache_data
def load_transactions() -> pd.DataFrame:
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'transactions.csv')
    return pd.read_csv(path, parse_dates=['date'])

@st.cache_data
def load_emission_factors() -> pd.DataFrame:
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'emission_factors.csv')
    return pd.read_csv(path)

CATEGORY_ICONS = {
    'Food Delivery': '🛵', 'Rideshare':  '🚗', 'Supermarket': '🛒',
    'Train':         '🚂', 'Coffee Shop':'☕', 'Fashion':     '👗',
    'Restaurant':    '🍽️', 'Fuel':       '⛽', 'Flight':      '✈️',
    'Hotel':         '🏨', 'Other':      '💳',
}

def confidence_badge_html(confidence: str) -> str:
    colors = {'High': '#166534', 'Medium': '#92400e', 'Low': '#7f1d1d'}
    bg = colors.get(confidence, '#374151')
    return (
        f'<span style="background:{bg};color:white;padding:3px 12px;'
        f'border-radius:999px;font-size:0.8rem;font-weight:700">'
        f'{confidence}</span>'
    )

def confidence_dot(confidence: str) -> str:
    return {'High': '🟢', 'Medium': '🟡', 'Low': '🔴'}.get(confidence, '⚪')
