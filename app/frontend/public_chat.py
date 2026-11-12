import streamlit as st
from app.frontend.components.api_client import client


def render_public_chat():
    st.markdown('<div class="main-header">🌐 Public Chatbot Preview</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-sub">Experience the public-facing interface that external visitors and embedded widgets interact with.</div>', unsafe_allow_html=True)

    bots = client.list_chatbots()
    published_bots = [b for b in bots if b.get("is_published")]

    if not published_bots:
        st.warning("No chatbots are currently published. Go to **My Chatbots** or the **Chatbot Builder** and toggle 'Published' to test the public interface.")
        return

    bot_map = {b["share_token"]: f"{b.get('bot_avatar', '🤖')} {b['name']}" for b in published_bots}
    selected_token = st.selectbox(
        "Select Published Chatbot",
        options=list(bot_map.keys()),
        format_func=lambda x: bot_map[x]
    )

    pub_bot = client.get_public_chatbot(selected_token)
    if not pub_bot:
        st.error("Could not fetch public chatbot details.")
        return

    brand_color = pub_bot.get("branding_color", "#4F46E5")
    avatar = pub_bot.get("bot_avatar", "🤖")

    st.markdown(f"""
        <div style="background-color: {brand_color}; color: white; padding: 18px 24px; border-radius: 12px; margin-bottom: 20px;">
            <div style="display:flex; align-items:center; gap: 14px;">
                <span style="font-size: 32px;">{avatar}</span>
                <div>
                    <h2 style="margin: 0; font-size: 20px; color: white;">{pub_bot['name']}</h2>
                    <p style="margin: 4px 0 0 0; font-size: 13px; opacity: 0.9;">{pub_bot.get('description', '')}</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    session_key = f"public_chat_{selected_token}"
    if session_key not in st.session_state:
        st.session_state[session_key] = [
            {"role": "assistant", "content": pub_bot.get("welcome_message", "Hello! How can I assist you today?")}
        ]

    for msg in st.session_state[session_key]:
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else avatar):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Ask a question..."):
        st.session_state[session_key].append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar=avatar):
            with st.spinner("Answering..."):
                resp = client.send_public_chat(
                    share_token=selected_token,
                    message=user_input,
                    session_id=f"pub_session_{selected_token}"
                )
                if resp:
                    ans = resp["answer"]
                    st.markdown(ans)
                    st.session_state[session_key].append({"role": "assistant", "content": ans})
                else:
                    st.error("Failed to receive response from assistant.")

