import streamlit as st
from app.frontend.components.api_client import client


def render_knowledge_manager():
    st.markdown('<div class="main-header">📚 Knowledge Sources Manager</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-sub">Upload, inspect, and manage grounded document corpora across your chatbots.</div>', unsafe_allow_html=True)

    bots = client.list_chatbots()
    if not bots:
        st.info("No chatbots found. Please create a chatbot first before uploading documents.")
        return

    bot_options = {b["id"]: f"{b.get('bot_avatar', '🤖')} {b['name']}" for b in bots}
    active_bot_id = st.session_state.get("active_bot_id")
    if not active_bot_id or active_bot_id not in bot_options:
        active_bot_id = list(bot_options.keys())[0]

    selected_bot_id = st.selectbox(
        "Select Target Chatbot",
        options=list(bot_options.keys()),
        format_func=lambda x: bot_options[x],
        index=list(bot_options.keys()).index(active_bot_id)
    )
    st.session_state["active_bot_id"] = selected_bot_id

    st.markdown("### Upload Knowledge Documents")
    uploaded_files = st.file_uploader(
        "Add documents to this chatbot's knowledge base",
        accept_multiple_files=True,
        type=["pdf", "docx", "txt", "csv", "xlsx", "pptx", "md", "json"]
    )

    enable_ocr = st.checkbox("Enable OCR fallback for scanned PDFs", value=False)

    if uploaded_files:
        if st.button("Upload & Index Files 🚀", type="primary"):
            with st.spinner("Extracting content, generating chunks, and indexing into isolated ChromaDB collection..."):
                file_tuples = [
                    ("files", (f.name, f.getvalue(), f.type or "application/octet-stream"))
                    for f in uploaded_files
                ]
                results = client.upload_files(selected_bot_id, file_tuples, enable_ocr=enable_ocr)
                success_count = sum(1 for r in results if r.get("status") == "indexed")
                if success_count > 0:
                    st.success(f"Successfully processed {success_count} file(s)!")
                for r in results:
                    if r.get("status") != "indexed":
                        st.error(f"{r.get('filename')}: {r.get('message')}")
                st.rerun()

    st.markdown("---")
    st.markdown("### Indexed Documents")
    docs = client.list_documents(selected_bot_id)
    if not docs:
        st.info("No documents indexed yet for this chatbot.")
    else:
        for doc in docs:
            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
            with c1:
                st.markdown(f"**{doc['filename']}**")
                st.caption(f"ID: `{doc['id']}` | Added: {doc['created_at'][:10]}")
            with c2:
                st.markdown(f"`{doc['file_type']}`")
            with c3:
                st.markdown(f"**{doc['total_chunks']}** chunks")
            with c4:
                st.markdown(f"{doc['file_size_bytes'] / 1024:.1f} KB")
            with c5:
                if st.button("🗑️ Remove", key=f"km_del_{doc['id']}"):
                    client.delete_document(selected_bot_id, doc["id"])
                    st.toast(f"Removed {doc['filename']}")
                    st.rerun()
            st.divider()

