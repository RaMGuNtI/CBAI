import streamlit as st
import os
from pathlib import Path
from app.core.config import settings
from app.core.security import mask_api_key


def render_settings():
    st.markdown('<div class="main-header">⚙️ System & Model Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-sub">Configure LLM providers, API keys, storage directories, and system thresholds.</div>', unsafe_allow_html=True)

    st.subheader("LLM Provider Configuration")
    st.caption("Provide your Google Gemini API key or OpenAI key. If left blank, the built-in grounded mock LLM generator is utilized for full offline functionality.")

    gemini_key = st.text_input(
        "Google Gemini API Key",
        value=settings.GEMINI_API_KEY,
        type="password",
        placeholder="AIzaSy..."
    )

    openai_key = st.text_input(
        "OpenAI API Key (Optional)",
        value=settings.OPENAI_API_KEY,
        type="password",
        placeholder="sk-..."
    )

    default_prov = st.selectbox(
        "Default LLM Provider",
        ["gemini", "openai", "mock"],
        index=["gemini", "openai", "mock"].index(settings.DEFAULT_LLM_PROVIDER)
    )

    if st.button("💾 Save Environment Settings", type="primary"):
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        lines = [
            f"GEMINI_API_KEY={gemini_key}\n",
            f"OPENAI_API_KEY={openai_key}\n",
            f"DEFAULT_LLM_PROVIDER={default_prov}\n"
        ]
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        os.environ["GEMINI_API_KEY"] = gemini_key
        os.environ["OPENAI_API_KEY"] = openai_key
        settings.GEMINI_API_KEY = gemini_key
        settings.OPENAI_API_KEY = openai_key
        settings.DEFAULT_LLM_PROVIDER = default_prov

        st.success("Settings saved to .env and updated in current session!")

    st.markdown("---")
    st.subheader("Storage & Vector Store Health")
    st.write(f"📁 **Storage Directory:** `{settings.STORAGE_DIR}`")
    st.write(f"📂 **Documents Path:** `{settings.DOCUMENTS_DIR}`")
    st.write(f"🧬 **ChromaDB Path:** `{settings.CHROMA_PERSIST_DIR}`")
    st.write(f"💾 **Database URL:** `{settings.DATABASE_URL}`")

