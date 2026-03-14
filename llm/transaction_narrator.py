"""
Smart Transaction Narrative — structured JSON output via Cohere.
Uses a multi-step refined prompt (prompt engineering iteration is
the non-straightforward element). Python post-processes the JSON
output to drive an eco-score card and tip cards in the UI.
"""
import cohere
import json
import re
import streamlit as st


@st.cache_resource
def _get_client():
    return cohere.ClientV2(st.secrets["COHERE_API_KEY"])


def _build_prompt(transaction: dict, result: dict) -> str:
    """
    Carefully engineered prompt (refined through multiple iterations) that:
    1. Provides rich transaction context
    2. Provides real-world benchmarks for grounding
    3. Enforces strict JSON-only output
    4. Specifies calibration rules for eco_score to avoid generic middle values
    """
    swap = result.get("swap_suggestion")
    swap_text = (
        f"A swap exists: {swap['tip']} — saves {swap['saving_kg']} kg CO2e."
        if swap else "No direct swap available."
    )

    return f"""You are a carbon footprint data analyst for a fintech app.
Analyse the transaction below and return ONLY valid JSON — no explanation, no markdown fences.

TRANSACTION DATA:
  Merchant:         {transaction['merchant']}
  Category:         {transaction['category']}
  Amount:           €{transaction['amount_eur']:.2f}
  CO2e estimate:    {result['co2e_kg']} kg
  Confidence:       {result['confidence']}
  Emission factor:  {result['emission_factor']} kg CO2e per EUR (source: {result['source']})
  {swap_text}

CALIBRATION BENCHMARKS:
  - Train (Renfe)        ≈ 0.04 kg CO2e/EUR   → eco_score 9-10
  - Coffee shop          ≈ 0.12 kg CO2e/EUR   → eco_score 7-8
  - Supermarket          ≈ 0.15 kg CO2e/EUR   → eco_score 6-7
  - Rideshare (Uber)     ≈ 0.18 kg CO2e/EUR   → eco_score 5-6
  - Food delivery (Glovo)≈ 0.21 kg CO2e/EUR   → eco_score 3-5
  - Flight               ≈ 1.45 kg CO2e/EUR   → eco_score 0-2

INSTRUCTIONS:
- eco_score: integer 0-10 calibrated strictly against the benchmarks above
- impact_level: one of "Very Low", "Low", "Moderate", "High", "Very High"
- narrative: 2 sentences max, human-friendly, mention what drives the CO2e
- three_tips: specific to this exact category, not generic
- comparison_context: compare to something tangible (e.g. "equivalent to driving X km")

Return ONLY this JSON:
{{
  "narrative": "...",
  "eco_score": <0-10>,
  "impact_level": "...",
  "three_tips": ["...", "...", "..."],
  "comparison_context": "..."
}}"""


def _parse_json(raw: str) -> dict:
    """Robustly parse JSON from LLM response, handling markdown fences."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {
        "narrative":          "Unable to generate narrative.",
        "eco_score":          5,
        "impact_level":       "Moderate",
        "three_tips":         ["Reduce frequency", "Choose alternatives", "Track progress"],
        "comparison_context": "Comparison unavailable.",
    }


def get_transaction_narrative(transaction: dict, result: dict) -> dict:
    """
    Call Cohere to generate a structured carbon narrative.

    Args:
        transaction: dict — merchant, category, amount_eur
        result:      dict — from estimate_co2e()

    Returns:
        dict — narrative, eco_score, impact_level, three_tips, comparison_context
    """
    client   = _get_client()
    prompt   = _build_prompt(transaction, result)

    response = client.chat(
        model="command-a-03-2025",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,    # Low temperature → consistent structured output
    )

    raw = response.message.content[0].text
    return _parse_json(raw)
