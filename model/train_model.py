"""
Offline training script — run once to produce carbon_model.pkl
Usage: python model/train_model.py
"""
import os
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

np.random.seed(42)

CATEGORIES = [
    'Food Delivery', 'Rideshare', 'Supermarket', 'Train',
    'Coffee Shop', 'Fashion', 'Restaurant', 'Fuel', 'Flight', 'Other'
]

BASE_CONFIDENCE = {
    'Food Delivery': 'Low',   'Rideshare': 'Medium', 'Supermarket': 'Medium',
    'Train': 'High',          'Coffee Shop': 'Medium','Fashion': 'Low',
    'Restaurant': 'Medium',   'Fuel': 'High',         'Flight': 'Medium',
    'Other': 'Low'
}

records = []
for _ in range(600):
    cat            = np.random.choice(CATEGORIES)
    amount         = np.random.uniform(3, 200)
    merchant_known = np.random.choice([0, 1], p=[0.3, 0.7])

    if cat in ['Food Delivery', 'Fashion'] and amount > 50:
        conf = 'Low'
    elif merchant_known and cat in ['Train', 'Fuel']:
        conf = 'High'
    elif merchant_known:
        conf = BASE_CONFIDENCE[cat]
    else:
        conf = 'Low'

    noise = np.random.random()
    if noise > 0.85 and conf == 'High':   conf = 'Medium'
    if noise > 0.90 and conf == 'Medium': conf = 'Low'

    records.append({'category': cat, 'amount': amount,
                    'merchant_known': merchant_known, 'confidence': conf})

df = pd.DataFrame(records)
le = LabelEncoder()
df['cat_enc']    = le.fit_transform(df['category'])
df['amount_log'] = np.log1p(df['amount'])

X = df[['cat_enc', 'amount_log', 'merchant_known']]
y = df['confidence']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

clf = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42)
clf.fit(X_train, y_train)

print("=== Model Performance ===")
print(classification_report(y_test, clf.predict(X_test)))

os.makedirs('model', exist_ok=True)
joblib.dump({'model': clf, 'label_encoder': le}, 'model/carbon_model.pkl')
print("✅ Saved → model/carbon_model.pkl")
