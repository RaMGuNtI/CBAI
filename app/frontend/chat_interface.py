import os
import streamlit as st
from pathlib import Path
from app.frontend.components.api_client import client
from app.core.config import settings


def render_chat_interface():
    st.markdown('<div class="main-header">💬 Interactive Chat Testing</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-sub">Real-time conversational sandbox with source document citations and retrieved chunk inspection.</div>', unsafe_allow_html=True)

    # API Key status check
    current_key = os.getenv("GEMINI_API_KEY", "") or getattr(settings, "GEMINI_API_KEY", "")
    if current_key:
        st.markdown(
            '<div style="background:#ECFDF5; border-left:4px solid #10B981; padding:8px 14px; border-radius:6px; font-size:13px; color:#065F46; margin-bottom:14px;">'
            '🟢 <b>Live LLM Active:</b> Responses are generated live via Google Gemini API.'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        with st.expander("🔑 Google Gemini API Key Not Found — Click to Enter Key & Activate Live LLM", expanded=True):
            st.info("Without an API key, CustomBot AI operates in **grounded offline mode** (answers are structured directly from retrieved chunks). Enter your Gemini API key below to unlock live conversational reasoning.")
            k_col1, k_col2 = st.columns([3, 1])
            with k_col1:
                entered_key = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...", label_visibility="collapsed")
            with k_col2:
                if st.button("Save & Connect ⚡", type="primary", use_container_width=True):
                    if entered_key.strip():
                        env_file = Path(__file__).resolve().parent.parent.parent / ".env"
                        with open(env_file, "a", encoding="utf-8") as f:
                            f.write(f"\nGEMINI_API_KEY={entered_key.strip()}\n")
                        os.environ["GEMINI_API_KEY"] = entered_key.strip()
                        settings.GEMINI_API_KEY = entered_key.strip()
                        st.success("Gemini API Key activated successfully!")
                        st.rerun()

    bots = client.list_chatbots()
    if not bots:
        st.warning("No chatbots available. Please create a chatbot first!")
        if st.button("➕ Create Chatbot"):
            st.session_state["nav_selection"] = "Create Chatbot"
            st.rerun()
        return

    # Select active chatbot
    bot_names = {b["id"]: f"{b.get('bot_avatar', '🤖')} {b['name']} ({b.get('domain', 'General')})" for b in bots}
    active_bot_id = st.session_state.get("active_bot_id")
    if not active_bot_id or active_bot_id not in bot_names:
        active_bot_id = list(bot_names.keys())[0]
        st.session_state["active_bot_id"] = active_bot_id

    col_sel, col_action = st.columns([3, 1])
    with col_sel:
        selected_id = st.selectbox(
            "Active Chatbot",
            options=list(bot_names.keys()),
            format_func=lambda x: bot_names[x],
            index=list(bot_names.keys()).index(active_bot_id)
        )
        if selected_id != active_bot_id:
            st.session_state["active_bot_id"] = selected_id
            st.rerun()

    active_bot = client.get_chatbot(selected_id)
    session_key = f"chat_history_{selected_id}"
    backend_session_id = f"session_{selected_id}"

    with col_action:
        st.write("")
        st.write("")
        if st.button("🧹 Clear Chat History", use_container_width=True):
            client.clear_conversation(selected_id, backend_session_id)
            if session_key in st.session_state:
                st.session_state[session_key] = []
            st.toast("Conversation history cleared.")
            st.rerun()

    # Welcome message banner
    if active_bot:
        st.markdown(f"""
            <div class="callout-box">
                <b>{active_bot.get('bot_avatar', '🤖')} {active_bot['name']}</b>: {active_bot.get('welcome_message', 'Hello!')}
            </div>
        """, unsafe_allow_html=True)

    # Initialize local message list from backend or state
    if session_key not in st.session_state:
        st.session_state[session_key] = []
        # Attempt to load from backend
        hist = client.get_conversation_history(selected_id, backend_session_id)
        if hist and "messages" in hist:
            for m in hist["messages"]:
                st.session_state[session_key].append({
                    "role": m["role"],
                    "content": m["content"],
                    "sources": m.get("sources_json", []),
                    "latency_ms": m.get("latency_ms", 0.0)
                })

    # Render conversation
    for msg in st.session_state[session_key]:
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else active_bot.get("bot_avatar", "🤖")):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander(f"📚 Verified Sources ({len(msg['sources'])} chunks)", expanded=False):
                    for s in msg["sources"]:
                        st.markdown(f"**Document:** `{s.get('filename')}` &nbsp;|&nbsp; **Page:** `{s.get('page_number')}` &nbsp;|&nbsp; **Score:** `{s.get('similarity')}`")
                        st.caption(s.get("snippet", ""))

    # Input Box
    if user_prompt := st.chat_input("Type your question..."):
        # Display user message
        st.session_state[session_key].append({"role": "user", "content": user_prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_prompt)

        # Generate assistant response
        with st.chat_message("assistant", avatar=active_bot.get("bot_avatar", "🤖")):
            with st.spinner("Retrieving knowledge base & generating response..."):
                resp = client.send_chat_message(
                    chatbot_id=selected_id,
                    message=user_prompt,
                    session_id=backend_session_id
                )

                if resp:
                    answer = resp["answer"]
                    sources = resp.get("sources", [])
                    st.markdown(answer)

                    if sources:
                        with st.expander(f"📚 Verified Sources ({len(sources)} chunks)", expanded=True):
                            for s in sources:
                                st.markdown(f"**Document:** `{s.get('filename')}` &nbsp;|&nbsp; **Page:** `{s.get('page_number')}` &nbsp;|&nbsp; **Score:** `{s.get('similarity')}`")
                                st.caption(s.get("snippet", ""))

                    st.caption(f"⚡ Latency: {resp.get('latency_ms', 0)}ms | Provider: {resp.get('provider')} | Estimated Tokens: {resp.get('tokens_used')}")

                    st.session_state[session_key].append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "latency_ms": resp.get("latency_ms", 0.0)
                    })
                else:
                    st.error("Failed to generate response. Backend may be offline.")

