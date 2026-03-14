"""
Carbon AI Advisor — Cohere tool-use agent (multi-call agentic loop).
The LLM autonomously decides which Python functions to call,
retrieves real transaction data as tool results, then synthesises
a personalised, data-grounded answer.
"""
import cohere
import json
import streamlit as st
from model.predict import get_monthly_summary, SWAP_OPTIONS
from utils.helpers import load_transactions

# ── Tool schemas (Cohere v2 / OpenAI-compatible format) ──────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_monthly_summary",
            "description": (
                "Returns the user's total CO2e footprint for February 2026, "
                "broken down by category and top 5 merchants."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_transactions",
            "description": "Returns the N highest-CO2e transactions this month.",
            "parameters": {
                "type": "object",
                "properties": {
                    "n": {"type": "integer", "description": "How many to return (default 5)"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_swap_suggestions",
            "description": (
                "Returns ranked behavioural swaps the user can make "
                "with estimated CO2e savings for each."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_goal_progress",
            "description": "Returns progress toward the user's monthly CO2e budget.",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_kg": {
                        "type": "number",
                        "description": "Monthly budget in kg CO2e (default 35)",
                    }
                },
                "required": [],
            },
        },
    },
]

# ── Tool implementations ──────────────────────────────────────────────────────
def _get_monthly_summary():
    s = get_monthly_summary(load_transactions())
    return {
        "total_co2e_kg":  s["total_co2e"],
        "by_category":    s["by_category"].to_dict(),
        "top_merchants":  s["by_merchant"].to_dict(),
        "n_transactions": len(s["transactions"]),
    }

def _get_top_transactions(n=5):
    s   = get_monthly_summary(load_transactions())
    df  = s["transactions"].sort_values("co2e_kg", ascending=False).head(n)
    return df[["merchant", "category", "amount_eur", "co2e_kg", "confidence"]].to_dict(orient="records")

def _get_swap_suggestions():
    s    = get_monthly_summary(load_transactions())
    df   = s["transactions"]
    out  = []
    for cat, swap in SWAP_OPTIONS.items():
        rows = df[df["category"] == cat]
        if len(rows):
            total   = rows["co2e_kg"].sum()
            saving  = round(total * swap["saving_pct"], 2)
            out.append({
                "category":           cat,
                "current_co2e_kg":    round(total, 2),
                "swap_to":            swap["swap_to"],
                "potential_saving_kg": saving,
                "tip":                swap["tip"],
            })
    return sorted(out, key=lambda x: x["potential_saving_kg"], reverse=True)

def _get_goal_progress(goal_kg=35):
    s           = get_monthly_summary(load_transactions())
    total       = s["total_co2e"]
    projected   = total / 19 * 28      # scale 19 elapsed days → 28
    return {
        "goal_kg":               goal_kg,
        "current_co2e_kg":       total,
        "remaining_kg":          round(max(goal_kg - total, 0), 2),
        "projected_month_end_kg": round(projected, 2),
        "on_track":              projected < goal_kg,
        "pct_used":              round(total / goal_kg * 100, 1),
    }

TOOL_MAP = {
    "get_monthly_summary":  _get_monthly_summary,
    "get_top_transactions":  _get_top_transactions,
    "get_swap_suggestions":  _get_swap_suggestions,
    "get_goal_progress":     _get_goal_progress,
}

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM = """You are a personal carbon footprint advisor embedded in the Revolut Carbon Receipt app.
You have tools that access the user's real transaction data for February 2026.
ALWAYS call at least one tool before answering to ground your response in actual data.
Be specific, friendly, and concise. Always quantify CO2e savings in kg when suggesting changes.
Format responses with clear sections using markdown. Never make up numbers."""

# ── Agentic loop ──────────────────────────────────────────────────────────────
@st.cache_resource
def _get_client():
    return cohere.ClientV2(st.secrets["COHERE_API_KEY"])

def run_agent(user_message: str, chat_history: list) -> tuple[str, list]:
    """
    One turn of the tool-use agent.
    Loops until the model stops calling tools and returns a final answer.

    Returns:
        (assistant_reply: str, updated_history: list)
    """
    client   = _get_client()
    messages = (
        [{"role": "system", "content": SYSTEM}]
        + chat_history
        + [{"role": "user", "content": user_message}]
    )

    # ── Agentic loop ──────────────────────────────────────────────────────────
    while True:
        response = client.chat(
            model="command-a-03-2025",
            messages=messages,
            tools=TOOLS,
        )

        # No more tool calls → final answer
        if not response.message.tool_calls:
            break

        # Append assistant's tool-call turn
        messages.append({
            "role":       "assistant",
            "tool_calls": response.message.tool_calls,
            "tool_plan":  getattr(response.message, "tool_plan", ""),
        })

        # Execute each tool and append results
        for tc in response.message.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            except (json.JSONDecodeError, TypeError):
                fn_args = {}

            result = TOOL_MAP[fn_name](**fn_args) if fn_name in TOOL_MAP else {"error": f"Unknown tool: {fn_name}"}

            messages.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      json.dumps(result),
            })

    reply = (
        response.message.content[0].text
        if response.message.content
        else "I couldn't generate a response."
    )

    updated_history = chat_history + [
        {"role": "user",      "content": user_message},
        {"role": "assistant", "content": reply},
    ]
    return reply, updated_history
