import sys
from pathlib import Path

# Ensure project root is at the head of sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
root_str = str(ROOT_DIR)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

# Remove the script directory from sys.path if Streamlit prepended it, preventing app.py from shadowing the 'app' package
script_dir = str(Path(__file__).resolve().parent)
while script_dir in sys.path:
    sys.path.remove(script_dir)

import streamlit as st
from app.frontend.components.ui import apply_saas_theme
from app.frontend.dashboard import render_dashboard
from app.frontend.chatbot_builder import render_chatbot_builder
from app.frontend.chat_interface import render_chat_interface
from app.frontend.knowledge_manager import render_knowledge_manager
from app.frontend.evaluation_view import render_evaluation_view
from app.frontend.public_chat import render_public_chat
from app.frontend.settings_view import render_settings
from app.frontend.components.api_client import client

st.set_page_config(
    page_title="CustomBot AI — No-Code RAG Chatbot Builder",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply sleek SaaS CSS styling
apply_saas_theme()

# Navigation handling
if "nav_selection" not in st.session_state:
    st.session_state["nav_selection"] = "Dashboard"

NAV_OPTIONS = [
    "Dashboard",
    "My Chatbots",
    "Create Chatbot",
    "Chat Interface",
    "Knowledge Sources",
    "RAG Evaluation",
    "Public Preview",
    "Settings"
]

NAV_ICONS = {
    "Dashboard": "📊",
    "My Chatbots": "🤖",
    "Create Chatbot": "🛠️",
    "Chat Interface": "💬",
    "Knowledge Sources": "📚",
    "RAG Evaluation": "🎯",
    "Public Preview": "🌐",
    "Settings": "⚙️"
}

with st.sidebar:
    st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom: 20px;">
            <span style="font-size:32px;">🤖</span>
            <div>
                <h2 style="margin:0; font-size:18px; font-weight:700; color:#1F2937;">CustomBot AI</h2>
                <span style="font-size:12px; color:#6B7280;">No-Code RAG Platform</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    current_nav = st.session_state["nav_selection"]
    if current_nav not in NAV_OPTIONS:
        current_nav = "Dashboard"

    selected_nav = st.radio(
        "Navigation",
        options=NAV_OPTIONS,
        format_func=lambda x: f"{NAV_ICONS.get(x, '')} {x}",
        index=NAV_OPTIONS.index(current_nav),
        label_visibility="collapsed"
    )

    if selected_nav != st.session_state["nav_selection"]:
        st.session_state["nav_selection"] = selected_nav
        st.rerun()

    st.markdown("---")
    is_online = client.is_backend_online()
    if is_online:
        st.markdown('<span style="color:#059669; font-size:13px; font-weight:600;">● Backend Online (FastAPI)</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span style="color:#DC2626; font-size:13px; font-weight:600;">○ Backend Connecting...</span>', unsafe_allow_html=True)

    st.caption("CustomBot AI v1.0.0")

# Route to selected page
nav = st.session_state["nav_selection"]

if nav == "Dashboard":
    render_dashboard()
elif nav == "My Chatbots":
    st.session_state["nav_selection"] = "Dashboard"
    render_dashboard()
elif nav == "Create Chatbot":
    render_chatbot_builder()
elif nav == "Chat Interface":
    render_chat_interface()
elif nav == "Knowledge Sources":
    render_knowledge_manager()
elif nav == "RAG Evaluation":
    render_evaluation_view()
elif nav == "Public Preview":
    render_public_chat()
elif nav == "Settings":
    render_settings()

