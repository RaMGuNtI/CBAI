import streamlit as st
from app.frontend.components.ui import render_metric_card
from app.frontend.components.api_client import client


def render_dashboard():
    st.markdown('<div class="main-header">📊 Platform Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-sub">Monitor your conversational AI bots, knowledge sources, and real-time interaction metrics.</div>', unsafe_allow_html=True)

    # Backend status banner
    is_online = client.is_backend_online()
    if not is_online:
        st.warning("⚠️ FastAPI Backend is offline or starting up. Ensure the backend server is running on port 8000.")

    metrics = client.get_dashboard_metrics()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Total Chatbots", metrics.get("total_chatbots", 0), icon="🤖")
    with col2:
        render_metric_card("Indexed Docs", metrics.get("total_documents", 0), icon="📚")
    with col3:
        render_metric_card("Conversations", metrics.get("total_conversations", 0), icon="💬")
    with col4:
        render_metric_card("Total Questions", metrics.get("total_questions", 0), icon="⚡")

    st.markdown("---")

    # Header with Quick Action
    d_col1, d_col2 = st.columns([4, 1])
    with d_col1:
        st.subheader("Recently Created Chatbots")
    with d_col2:
        if st.button("➕ New Chatbot", type="primary", use_container_width=True):
            st.session_state["nav_selection"] = "Create Chatbot"
            st.session_state["editing_bot_id"] = None
            st.session_state["wizard_step"] = 1
            st.rerun()

    recent_bots = metrics.get("recent_chatbots", [])
    if not recent_bots:
        st.info("No chatbots found yet. Click '**➕ New Chatbot**' above to build your first RAG chatbot in minutes without any code!")
    else:
        for bot in recent_bots:
            bot_id = bot.get("id")
            name = bot.get("name")
            desc = bot.get("description") or "No description provided."
            domain = bot.get("domain", "General Purpose")
            is_pub = bot.get("is_published", False)
            doc_cnt = bot.get("document_count", 0)
            avatar = bot.get("bot_avatar", "🤖")

            status_badge = (
                '<span class="bot-badge-pub">● Published</span>'
                if is_pub
                else '<span class="bot-badge-priv">○ Draft / Private</span>'
            )

            with st.container():
                st.markdown(f"""
                    <div class="bot-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="display:flex; align-items:center; gap:12px;">
                                <span style="font-size:28px;">{avatar}</span>
                                <div>
                                    <h3 style="margin:0; font-size:18px; font-weight:600;">{name}</h3>
                                    <p style="margin:2px 0 0 0; color:#6B7280; font-size:13px;">Domain: <b>{domain}</b> &nbsp;|&nbsp; Documents: <b>{doc_cnt}</b></p>
                                </div>
                            </div>
                            <div>{status_badge}</div>
                        </div>
                        <p style="margin:12px 0 0 0; font-size:14px; color:#374151;">{desc}</p>
                    </div>
                """, unsafe_allow_html=True)

                b_col1, b_col2, b_col3, b_col4, b_col5 = st.columns([1, 1, 1, 1, 1])
                with b_col1:
                    if st.button(f"💬 Test Chat", key=f"dash_test_{bot_id}", use_container_width=True):
                        st.session_state["active_bot_id"] = bot_id
                        st.session_state["nav_selection"] = "Chat Interface"
                        st.rerun()
                with b_col2:
                    if st.button(f"📚 Knowledge", key=f"dash_docs_{bot_id}", use_container_width=True):
                        st.session_state["active_bot_id"] = bot_id
                        st.session_state["nav_selection"] = "Knowledge Sources"
                        st.rerun()
                with b_col3:
                    if st.button(f"⚙️ Edit Config", key=f"dash_edit_{bot_id}", use_container_width=True):
                        st.session_state["editing_bot_id"] = bot_id
                        st.session_state["nav_selection"] = "Create Chatbot"
                        st.session_state["wizard_step"] = 1
                        st.rerun()
                with b_col4:
                    if st.button(f"🎯 Evaluate", key=f"dash_eval_{bot_id}", use_container_width=True):
                        st.session_state["active_bot_id"] = bot_id
                        st.session_state["nav_selection"] = "RAG Evaluation"
                        st.rerun()
                with b_col5:
                    new_status = not is_pub
                    pub_label = "Unpublish" if is_pub else "Publish"
                    if st.button(pub_label, key=f"dash_pub_{bot_id}", use_container_width=True):
                        client.set_publish_status(bot_id, new_status)
                        st.toast(f"Updated status to {'Published' if new_status else 'Private'}")
                        st.rerun()
                st.write("")

