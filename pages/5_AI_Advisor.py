import streamlit as st
from llm.advisor_agent import run_agent

st.set_page_config(page_title="AI Advisor · Carbon", page_icon="🤖", layout="wide")
st.title("🤖 Carbon AI Advisor")
st.caption("Ask anything about your footprint — powered by Cohere + your real transaction data.")
st.divider()

# ── Session state ─────────────────────────────────────────────────────────────
if "chat_history"      not in st.session_state: st.session_state.chat_history      = []
if "messages_display"  not in st.session_state: st.session_state.messages_display  = []

# ── Suggested questions (shown when chat is empty) ────────────────────────────
# Suggestions always visible — collapsed after first use
suggestions = [
    "How can I cut my footprint by 20% this month?",
    "Which single change would save the most CO₂e?",
    "Am I on track to meet my 35 kg goal?",
    "What's driving most of my emissions?",
]

expanded = not bool(st.session_state.messages_display)
with st.expander("💡 Try asking:", expanded=expanded):
    c1, c2 = st.columns(2)
    for i, q in enumerate(suggestions):
        col = c1 if i % 2 == 0 else c2
        if col.button(q, use_container_width=True, key=f"sug_{i}"):
            st.session_state["prefill"] = q
            st.rerun()

# ── Chat messages ─────────────────────────────────────────────────────────────
for msg in st.session_state.messages_display:
    avatar = "🤖" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ── Input ─────────────────────────────────────────────────────────────────────
prefill    = st.session_state.pop("prefill", "")
user_input = st.chat_input("Ask about your carbon footprint...")
question   = user_input or prefill or None

if question:
    with st.chat_message("user", avatar="👤"):
        st.markdown(question)
    st.session_state.messages_display.append({"role": "user", "content": question})

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Checking your transactions..."):
            try:
                reply, updated = run_agent(question, st.session_state.chat_history)
                st.session_state.chat_history = updated
                st.markdown(reply)
                st.session_state.messages_display.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"⚠️ {e}")

# ── Clear ─────────────────────────────────────────────────────────────────────
if st.session_state.messages_display:
    if st.button("🗑️ Clear conversation"):
        st.session_state.chat_history     = []
        st.session_state.messages_display = []
        st.rerun()
