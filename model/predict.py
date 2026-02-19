"""
Prediction logic — fully separated from the Streamlit runtime.
Handles: emission factor lookup + ML confidence scoring + what-if calculations.
"""
import os
import numpy as np
import pandas as pd
import joblib

# ── Constants ──────────────────────────────────────────────────────────────
DELIVERY_MODE_FACTORS = {'Delivery': 1.0, 'Pickup': 0.78}

SWAP_OPTIONS = {
    'Food Delivery': {
        'swap_to': 'Pickup',
        'saving_pct': 0.22,
        'tip': 'Pick up instead of delivery (saves ~22% CO₂e)'
    },
    'Rideshare': {
        'swap_to': 'Train / Metro',
        'saving_pct': 0.75,
        'tip': 'Take public transport instead of rideshare (saves ~75%)'
    },
    'Flight': {
        'swap_to': 'Train',
        'saving_pct': 0.85,
        'tip': 'Consider train for short/medium distances (saves ~85%)'
    },
    'Fashion': {
        'swap_to': 'Second-hand',
        'saving_pct': 0.50,
        'tip': 'Buy second-hand or rent instead (saves ~50%)'
    },
}

# ── Module-level model cache (loaded once per worker process) ───────────────
_assets = None

def _get_assets():
    global _assets
    if _assets is None:
        base = os.path.dirname(__file__)
        pkg   = joblib.load(os.path.join(base, 'carbon_model.pkl'))
        ef_df = pd.read_csv(os.path.join(base, '..', 'data', 'emission_factors.csv'))
        _assets = (pkg['model'], pkg['label_encoder'], ef_df)
    return _assets

# ── Core functions ──────────────────────────────────────────────────────────
def get_emission_factor(category: str, ef_df: pd.DataFrame) -> dict:
    row = ef_df[ef_df['category'] == category]
    if row.empty:
        row = ef_df[ef_df['category'] == 'Other']
    r = row.iloc[0]
    return {
        'factor': r['emission_factor_per_eur'],
        'unit':   r['unit'],
        'source': r['source'],
        'confidence_base': r['confidence_base']
    }

def predict_confidence(category: str, amount: float,
                       merchant_known: bool, model, le) -> str:
    try:
        cat_enc = le.transform([category])[0]
    except ValueError:
        cat_enc = 0
    X = pd.DataFrame(
        [[cat_enc, np.log1p(amount), int(merchant_known)]],
        columns=['cat_enc', 'amount_log', 'merchant_known']
    )
    return model.predict(X)[0]

def estimate_co2e(transaction: dict, delivery_mode: str = None) -> dict:
    """
    Full pipeline:
      1. Lookup emission factor by category
      2. Multiply by spend amount
      3. Adjust for delivery mode if applicable
      4. Predict confidence via RandomForest
      5. Generate what-if swap suggestion

    Args:
        transaction: dict with keys merchant, category, amount_eur, merchant_known
        delivery_mode: 'Delivery' | 'Pickup' (Food Delivery category only)

    Returns:
        dict with co2e_kg, confidence, emission_factor, source,
              explanation, swap_suggestion, delivery_mode
    """
    model, le, ef_df = _get_assets()
    ef   = get_emission_factor(transaction['category'], ef_df)
    co2e = transaction['amount_eur'] * ef['factor']

    if delivery_mode and transaction['category'] == 'Food Delivery':
        co2e *= DELIVERY_MODE_FACTORS.get(delivery_mode, 1.0)

    confidence = predict_confidence(
        transaction['category'],
        transaction['amount_eur'],
        transaction.get('merchant_known', True),
        model, le
    )

    swap = SWAP_OPTIONS.get(transaction['category'])
    swap_info = None
    if swap:
        swap_info = {
            'swap_to':   swap['swap_to'],
            'saving_kg': round(co2e * swap['saving_pct'], 2),
            'tip':       swap['tip']
        }

    return {
        'co2e_kg':         round(co2e, 2),
        'confidence':      confidence,
        'emission_factor': ef['factor'],
        'source':          ef['source'],
        'explanation': (
            f"Mapped **{transaction['category']}** → emission factor "
            f"**{ef['factor']} {ef['unit']}** (Source: {ef['source']}). "
            f"Confidence scored **{confidence}** by RandomForest model based "
            f"on category, spend amount, and merchant recognition."
        ),
        'swap_suggestion': swap_info,
        'delivery_mode':   delivery_mode,
    }

def get_monthly_summary(transactions_df: pd.DataFrame) -> dict:
    rows = []
    for _, row in transactions_df.iterrows():
        t = {
            'merchant':      row['merchant'],
            'category':      row['category'],
            'amount_eur':    row['amount_eur'],
            'merchant_known': True
        }
        r = estimate_co2e(t)
        rows.append({
            'id':         row['id'],
            'date':       row['date'],
            'merchant':   row['merchant'],
            'category':   row['category'],
            'amount_eur': row['amount_eur'],
            'co2e_kg':    r['co2e_kg'],
            'confidence': r['confidence'],
        })
    df = pd.DataFrame(rows)
    return {
        'total_co2e':   round(df['co2e_kg'].sum(), 2),
        'by_category':  df.groupby('category')['co2e_kg'].sum().sort_values(ascending=False),
        'by_merchant':  df.groupby('merchant')['co2e_kg'].sum().sort_values(ascending=False).head(5),
        'transactions': df,
    }
