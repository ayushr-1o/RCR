# 🌱 Revolut Personal Carbon Receipt

> ESADE PDAI Assignment 1 — Streamlit prototype demonstrating an AI-powered carbon footprint feature for Revolut.

## 💡 Concept
Adds a **Carbon View** on top of Revolut spending. Each transaction shows:
- Estimated **CO₂e** (merchant category × emission factor)
- **Confidence level** (RandomForest ML model)
- **What-if swaps** (e.g., pickup vs delivery)
- Monthly **dashboard**, **goal tracking** and an **editable action plan**

## 🚀 Setup
```bash
git clone https://github.com/ayushr-1o/RCR.git
cd RCR
pip install -r requirements.txt
python model/train_model.py   # one-time offline training → generates carbon_model.pkl
streamlit run app.py
```

## 🛠️ Tech Stack
| Layer | Tool |
|---|---|
| UI | Streamlit multi-page + custom CSS |
| ML | scikit-learn RandomForestClassifier |
| Charts | Plotly Express + Graph Objects (Indicator, Waterfall) |
| Custom component | `streamlit.components.v1.html` — SVG circular gauge |
| Data | Synthetic transactions + EPA Supply Chain Emission Factors v1.2 |

## 📊 Data Sources
- **EPA Supply Chain GHG Emission Factors v1.2** (kg CO₂e per USD, adapted to EUR)
- **DEFRA 2023 GHG Conversion Factors** — transport & food
- **ICAO Carbon Calculator** — flights

## 🤖 AI Pipeline
1. **Emission estimation** — rule-based lookup (merchant → category → factor × spend)
2. **Confidence scoring** — RandomForest trained on (category, amount, merchant_known) → High/Medium/Low
3. **What-if engine** — deterministic swap calculator (delivery, transport, fashion)
