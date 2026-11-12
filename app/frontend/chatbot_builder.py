import streamlit as st
import json
from app.frontend.components.api_client import client


DOMAINS = [
    "General Purpose",
    "Education",
    "E-commerce",
    "Healthcare information",
    "Customer Support",
    "HR and Recruitment",
    "Legal Information",
    "Technical Documentation",
    "Finance",
    "Custom Domain"
]

PERSONALITIES = [
    "Professional",
    "Friendly",
    "Casual",
    "Technical",
    "Academic",
    "Customer Support",
    "Custom"
]

TONES = [
    "Formal",
    "Neutral",
    "Friendly",
    "Conversational"
]

LANGUAGES = [
    "English",
    "Hindi",
    "Telugu",
    "Spanish",
    "French",
    "German",
    "Custom"
]

LENGTHS = [
    "Short",
    "Medium",
    "Detailed"
]

AUDIENCES = [
    "Beginner",
    "Intermediate",
    "Expert"
]

FORMATS = [
    "Structured Markdown",
    "Paragraphs",
    "Bullet Points",
    "Numbered Lists",
    "Tables",
    "JSON"
]


def render_chatbot_builder():
    editing_id = st.session_state.get("editing_bot_id")
    is_edit_mode = bool(editing_id)

    # Initialize or load bot state
    if "wizard_step" not in st.session_state:
        st.session_state["wizard_step"] = 1

    current_step = st.session_state["wizard_step"]

    # Header
    title = f"🛠️ {'Edit Chatbot' if is_edit_mode else 'Create New Chatbot'}"
    st.markdown(f'<div class="main-header">{title}</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-sub">Step-by-step no-code builder to construct and publish your grounded RAG assistant.</div>', unsafe_allow_html=True)

    # Step Wizard Indicator Navigation
    step_labels = [
        "1. Details",
        "2. Knowledge",
        "3. Domain",
        "4. Behaviour",
        "5. Response Format",
        "6. RAG Settings",
        "7. Test Preview",
        "8. Publish"
    ]

    pills_html = []
    for idx, label in enumerate(step_labels, 1):
        if idx == current_step:
            cls = "wizard-step wizard-step-active"
        elif idx < current_step:
            cls = "wizard-step wizard-step-done"
        else:
            cls = "wizard-step"
        pills_html.append(f'<span class="{cls}">{label}</span>')

    st.markdown("<div>" + "".join(pills_html) + "</div><br/>", unsafe_allow_html=True)

    # Load existing bot data if editing and not loaded yet
    bot_data = None
    if is_edit_mode:
        bot_data = client.get_chatbot(editing_id)
        if not bot_data:
            st.error("Chatbot could not be found.")
            return

    # ----------------------------------------------------
    # STEP 1: Basic Information
    # ----------------------------------------------------
    if current_step == 1:
        st.subheader("Step 1: Chatbot Identity & Purpose")
        st.caption("Provide a clear name and initial identity for your AI assistant.")

        default_name = bot_data.get("name", "") if bot_data else st.session_state.get("w_name", "")
        default_desc = bot_data.get("description", "") if bot_data else st.session_state.get("w_desc", "")
        default_purpose = bot_data.get("purpose", "") if bot_data else st.session_state.get("w_purpose", "")
        default_welcome = bot_data.get("welcome_message", "Hello! How can I assist you today?") if bot_data else st.session_state.get("w_welcome", "Hello! How can I assist you today?")
        default_avatar = bot_data.get("bot_avatar", "🤖") if bot_data else st.session_state.get("w_avatar", "🤖")
        default_color = bot_data.get("branding_color", "#4F46E5") if bot_data else st.session_state.get("w_color", "#4F46E5")

        col_a, col_b = st.columns([3, 1])
        with col_a:
            bot_name = st.text_input("Chatbot Name*", value=default_name, placeholder="e.g. Acme Support Assistant")
        with col_b:
            avatar = st.selectbox("Bot Avatar", ["🤖", "💼", "🩺", "🎓", "⚖️", "🛍️", "🛠️", "🚀"], index=0)

        bot_desc = st.text_area("Description", value=default_desc, placeholder="Brief overview of what this bot provides for your team or customers.", height=80)
        bot_purpose = st.text_input("Operational Purpose", value=default_purpose, placeholder="e.g. Answer customer warranty queries and product specifications.")
        bot_welcome = st.text_input("Welcome Message", value=default_welcome)
        branding_color = st.color_picker("Brand Accent Color", value=default_color)

        st.markdown("---")
        next_col, _ = st.columns([1, 4])
        with next_col:
            if st.button("Save & Next ➡️", type="primary", use_container_width=True):
                if not bot_name.strip():
                    st.error("Please enter a Chatbot Name.")
                else:
                    st.session_state["w_name"] = bot_name.strip()
                    st.session_state["w_desc"] = bot_desc.strip()
                    st.session_state["w_purpose"] = bot_purpose.strip()
                    st.session_state["w_welcome"] = bot_welcome.strip()
                    st.session_state["w_avatar"] = avatar
                    st.session_state["w_color"] = branding_color

                    # If not created yet in DB, create initial draft bot
                    if not is_edit_mode:
                        created = client.create_chatbot({
                            "name": bot_name.strip(),
                            "description": bot_desc.strip(),
                            "purpose": bot_purpose.strip(),
                            "welcome_message": bot_welcome.strip()
                        })
                        if created:
                            st.session_state["editing_bot_id"] = created["id"]
                            st.session_state["active_bot_id"] = created["id"]
                    else:
                        client.update_chatbot(editing_id, {
                            "name": bot_name.strip(),
                            "description": bot_desc.strip(),
                            "purpose": bot_purpose.strip(),
                            "welcome_message": bot_welcome.strip(),
                            "bot_avatar": avatar,
                            "branding_color": branding_color
                        })

                    st.session_state["wizard_step"] = 2
                    st.rerun()

    # ----------------------------------------------------
    # STEP 2: Upload Knowledge Sources
    # ----------------------------------------------------
    elif current_step == 2:
        bot_id = st.session_state.get("editing_bot_id")
        st.subheader("Step 2: Upload Knowledge Sources")
        st.caption("Upload documents that your chatbot will use as its verified source of truth.")

        st.info("Supported formats: **PDF, DOCX, TXT, CSV, XLSX, PPTX, Markdown (.md), and JSON**. Upload limit: 25MB per file.")

        uploaded_files = st.file_uploader(
            "Choose knowledge files to ingest",
            accept_multiple_files=True,
            type=["pdf", "docx", "txt", "csv", "xlsx", "pptx", "md", "json"]
        )

        enable_ocr = st.checkbox("Enable OCR for scanned PDFs (requires tesseract binary on host)", value=False)

        if uploaded_files:
            if st.button("⚡ Process & Index Uploaded Files", type="primary"):
                with st.spinner("Processing text extraction, chunking, and isolated vector indexing..."):
                    file_tuples = [
                        ("files", (f.name, f.getvalue(), f.type or "application/octet-stream"))
                        for f in uploaded_files
                    ]
                    results = client.upload_files(bot_id, file_tuples, enable_ocr=enable_ocr)
                    success_count = sum(1 for r in results if r.get("status") == "indexed")
                    if success_count > 0:
                        st.success(f"Successfully processed and indexed {success_count} file(s)!")
                    for r in results:
                        if r.get("status") != "indexed":
                            st.error(f"Error on {r.get('filename')}: {r.get('message')}")

        st.markdown("#### Currently Indexed Knowledge Sources")
        docs = client.list_documents(bot_id) if bot_id else []
        if not docs:
            st.warning("No knowledge documents have been uploaded yet. You can upload documents now or proceed and add them later.")
        else:
            for doc in docs:
                d_col1, d_col2, d_col3, d_col4 = st.columns([3, 1, 1, 1])
                with d_col1:
                    st.write(f"📄 **{doc['filename']}** ({doc['file_type']})")
                with d_col2:
                    st.write(f"{doc['total_chunks']} chunks")
                with d_col3:
                    st.write(f"{doc['file_size_bytes'] / 1024:.1f} KB")
                with d_col4:
                    if st.button("🗑️ Delete", key=f"del_doc_{doc['id']}"):
                        client.delete_document(bot_id, doc["id"])
                        st.toast("Document removed.")
                        st.rerun()

        st.markdown("---")
        prev_col, _, next_col = st.columns([1, 3, 1])
        with prev_col:
            if st.button("⬅️ Back"):
                st.session_state["wizard_step"] = 1
                st.rerun()
        with next_col:
            if st.button("Next: Domain ➡️", type="primary", use_container_width=True):
                st.session_state["wizard_step"] = 3
                st.rerun()

    # ----------------------------------------------------
    # STEP 3: Chatbot Domain
    # ----------------------------------------------------
    elif current_step == 3:
        bot_id = st.session_state.get("editing_bot_id")
        cfg = bot_data.get("configuration", {}) if bot_data else {}
        current_domain = bot_data.get("domain", "General Purpose") if bot_data else "General Purpose"
        current_domain_desc = bot_data.get("domain_description", "") if bot_data else ""

        st.subheader("Step 3: Select Chatbot Domain")
        st.caption("Selecting a domain optimizes the baseline instructions and reasoning context for your vertical.")

        selected_domain = st.selectbox(
            "Select Industry / Domain Category",
            DOMAINS,
            index=DOMAINS.index(current_domain) if current_domain in DOMAINS else 0
        )

        domain_desc = ""
        if selected_domain == "Custom Domain":
            domain_desc = st.text_area(
                "Describe your custom domain & operational scope*",
                value=current_domain_desc,
                placeholder="e.g. Specialized internal chemical engineering guidelines for solvent distillation.",
                height=100
            )

        st.markdown("---")
        prev_col, _, next_col = st.columns([1, 3, 1])
        with prev_col:
            if st.button("⬅️ Back"):
                st.session_state["wizard_step"] = 2
                st.rerun()
        with next_col:
            if st.button("Next: Behaviour ➡️", type="primary", use_container_width=True):
                client.update_chatbot(bot_id, {
                    "domain": selected_domain,
                    "domain_description": domain_desc
                })
                st.session_state["wizard_step"] = 4
                st.rerun()

    # ----------------------------------------------------
    # STEP 4: Chatbot Behaviour & Personality
    # ----------------------------------------------------
    elif current_step == 4:
        bot_id = st.session_state.get("editing_bot_id")
        cfg = bot_data.get("configuration", {}) if bot_data else {}

        st.subheader("Step 4: Customize Behaviour & Personality")
        st.caption("Tune persona traits, audience level, languages, and strict behavioral guidelines.")

        col1, col2 = st.columns(2)
        with col1:
            p_val = cfg.get("personality", "Professional")
            personality = st.selectbox("Personality", PERSONALITIES, index=PERSONALITIES.index(p_val) if p_val in PERSONALITIES else 0)

            t_val = cfg.get("tone", "Formal")
            tone = st.selectbox("Tone", TONES, index=TONES.index(t_val) if t_val in TONES else 0)

            l_val = cfg.get("language", "English")
            language = st.selectbox("Response Language", LANGUAGES, index=LANGUAGES.index(l_val) if l_val in LANGUAGES else 0)
            if language == "Custom":
                language = st.text_input("Specify Language Name", value="Spanish")

        with col2:
            len_val = cfg.get("response_length", "Medium")
            response_len = st.selectbox("Response Length", LENGTHS, index=LENGTHS.index(len_val) if len_val in LENGTHS else 1)

            aud_val = cfg.get("target_audience", "Intermediate")
            target_audience = st.selectbox("Target Audience", AUDIENCES, index=AUDIENCES.index(aud_val) if aud_val in AUDIENCES else 1)

        custom_instructions = st.text_area(
            "Custom System Instructions",
            value=cfg.get("custom_instructions", ""),
            placeholder="e.g. Always recommend checking user warranty before advising component replacement.",
            height=90
        )

        behavioral_restrictions = st.text_area(
            "Behavioral Restrictions & Boundaries",
            value=cfg.get("behavioral_restrictions", ""),
            placeholder="e.g. Never discuss internal competitor pricing or speculate on unreleased products.",
            height=90
        )

        st.markdown("---")
        prev_col, _, next_col = st.columns([1, 3, 1])
        with prev_col:
            if st.button("⬅️ Back"):
                st.session_state["wizard_step"] = 3
                st.rerun()
        with next_col:
            if st.button("Next: Response Format ➡️", type="primary", use_container_width=True):
                client.update_chatbot(bot_id, {
                    "configuration": {
                        "personality": personality,
                        "tone": tone,
                        "language": language,
                        "response_length": response_len,
                        "target_audience": target_audience,
                        "custom_instructions": custom_instructions,
                        "behavioral_restrictions": behavioral_restrictions
                    }
                })
                st.session_state["wizard_step"] = 5
                st.rerun()

    # ----------------------------------------------------
    # STEP 5: Response Format
    # ----------------------------------------------------
    elif current_step == 5:
        bot_id = st.session_state.get("editing_bot_id")
        cfg = bot_data.get("configuration", {}) if bot_data else {}

        st.subheader("Step 5: Configure Response Format & Grounding")
        st.caption("Determine the visual structure of responses and knowledge adherence rules.")

        fmt_val = cfg.get("response_format", "Structured Markdown")
        response_fmt = st.selectbox("Primary Response Format", FORMATS, index=FORMATS.index(fmt_val) if fmt_val in FORMATS else 0)

        json_schema_text = ""
        if response_fmt == "JSON":
            st.info("Define an optional JSON Schema. The generated JSON will be validated against this specification.")
            json_schema_text = st.text_area(
                "JSON Schema Specification",
                value=cfg.get("json_schema", '{\n  "type": "object",\n  "properties": {\n    "answer": {"type": "string"},\n    "confidence": {"type": "number"}\n  },\n  "required": ["answer"]\n}'),
                height=150
            )

        col1, col2 = st.columns(2)
        with col1:
            exclusive_knowledge = st.checkbox(
                "Strict Grounding (Exclusively answer from uploaded knowledge)",
                value=cfg.get("exclusive_knowledge", True),
                help="When enabled, the bot refuses to answer questions not covered by the documents."
            )
            enable_citations = st.checkbox(
                "Include Source Citations (Document name & page numbers)",
                value=cfg.get("enable_citations", True)
            )

        with col2:
            max_tokens = st.number_input("Max Output Tokens", min_value=128, max_value=4096, value=cfg.get("max_response_tokens", 1024), step=128)

        fallback_response = st.text_area(
            "Custom Fallback Response (When answer cannot be found in knowledge sources)",
            value=cfg.get("fallback_response", "I apologize, but I could not find relevant information in the provided knowledge base to answer your question."),
            height=80
        )

        st.markdown("---")
        prev_col, _, next_col = st.columns([1, 3, 1])
        with prev_col:
            if st.button("⬅️ Back"):
                st.session_state["wizard_step"] = 4
                st.rerun()
        with next_col:
            if st.button("Next: RAG Settings ➡️", type="primary", use_container_width=True):
                client.update_chatbot(bot_id, {
                    "configuration": {
                        "response_format": response_fmt,
                        "json_schema": json_schema_text,
                        "exclusive_knowledge": exclusive_knowledge,
                        "enable_citations": enable_citations,
                        "max_response_tokens": max_tokens,
                        "fallback_response": fallback_response
                    }
                })
                st.session_state["wizard_step"] = 6
                st.rerun()

    # ----------------------------------------------------
    # STEP 6: Configure RAG Retrieval Settings
    # ----------------------------------------------------
    elif current_step == 6:
        bot_id = st.session_state.get("editing_bot_id")
        cfg = bot_data.get("configuration", {}) if bot_data else {}

        st.subheader("Step 6: Configure RAG Retrieval Pipeline")
        st.caption("Sensible defaults are pre-configured. Open Advanced Settings if you wish to adjust retrieval mechanics.")

        col1, col2 = st.columns(2)
        with col1:
            chunk_size = st.slider("Chunk Size (characters)", min_value=100, max_value=2000, value=cfg.get("chunk_size", 500), step=50)
            chunk_overlap = st.slider("Chunk Overlap (characters)", min_value=0, max_value=400, value=cfg.get("chunk_overlap", 50), step=10)
            top_k = st.slider("Top-K Retrieved Chunks", min_value=1, max_value=10, value=cfg.get("top_k", 4))

        with col2:
            sim_thresh = st.slider("Similarity Threshold (0.0 - 1.0)", min_value=0.0, max_value=0.9, value=float(cfg.get("similarity_threshold", 0.25)), step=0.05)
            retrieval_strat = st.selectbox("Retrieval Strategy", ["similarity", "threshold", "mmr"], index=0)

        with st.expander("🛠️ Advanced Hybrid & Reranking Options", expanded=False):
            enable_hybrid = st.checkbox("Enable Hybrid Retrieval (Vector Cosine + BM25 Lexical Keyword Search)", value=cfg.get("enable_hybrid", False))
            enable_reranking = st.checkbox("Enable Query-Document Reranking", value=cfg.get("enable_reranking", False))
            embedding_model = st.selectbox("Embedding Model", ["all-MiniLM-L6-v2", "paraphrase-MiniLM-L3-v2"], index=0)

            llm_prov = st.selectbox("LLM Provider", ["gemini", "openai", "mock"], index=0)
            llm_model = st.text_input("LLM Model Name", value=cfg.get("llm_model", "gemini-1.5-flash"))

        st.markdown("---")
        prev_col, _, next_col = st.columns([1, 3, 1])
        with prev_col:
            if st.button("⬅️ Back"):
                st.session_state["wizard_step"] = 5
                st.rerun()
        with next_col:
            if st.button("Next: Test Preview ➡️", type="primary", use_container_width=True):
                client.update_chatbot(bot_id, {
                    "configuration": {
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap,
                        "top_k": top_k,
                        "similarity_threshold": sim_thresh,
                        "retrieval_strategy": retrieval_strat,
                        "enable_hybrid": enable_hybrid,
                        "enable_reranking": enable_reranking,
                        "embedding_model": embedding_model,
                        "llm_provider": llm_prov,
                        "llm_model": llm_model
                    }
                })
                st.session_state["wizard_step"] = 7
                st.rerun()

    # ----------------------------------------------------
    # STEP 7: Interactive Testing Preview
    # ----------------------------------------------------
    elif current_step == 7:
        bot_id = st.session_state.get("editing_bot_id")
        st.subheader("Step 7: Chatbot Testing Preview")
        st.caption("Interact with your newly configured chatbot before publishing.")

        preview_session = f"preview_{bot_id}"
        test_q = st.text_input("Ask a question to test your chatbot:", placeholder="e.g. What are the key details in the uploaded document?")

        if st.button("Ask Assistant 🚀", type="primary") and test_q:
            with st.spinner("Retrieving knowledge chunks and generating grounded response..."):
                resp = client.send_chat_message(bot_id, test_q, session_id=preview_session)
                if resp:
                    st.markdown("### Assistant Response")
                    st.markdown(resp["answer"])

                    st.caption(f"⚡ Latency: {resp.get('latency_ms', 0)}ms | Provider: {resp.get('provider')} | Estimated Tokens: {resp.get('tokens_used')}")

                    sources = resp.get("sources", [])
                    if sources:
                        with st.expander(f"📚 Retrieved Context & Sources ({len(sources)} chunks)", expanded=True):
                            for s in sources:
                                st.markdown(f"**Document:** `{s.get('filename')}` &nbsp;|&nbsp; **Page:** `{s.get('page_number')}` &nbsp;|&nbsp; **Similarity Score:** `{s.get('similarity')}`")
                                st.code(s.get("snippet", ""), language="markdown")
                else:
                    st.error("Failed to generate response. Please ensure backend is running.")

        st.markdown("---")
        prev_col, _, next_col = st.columns([1, 3, 1])
        with prev_col:
            if st.button("⬅️ Back"):
                st.session_state["wizard_step"] = 6
                st.rerun()
        with next_col:
            if st.button("Next: Publish & Share ➡️", type="primary", use_container_width=True):
                st.session_state["wizard_step"] = 8
                st.rerun()

    # ----------------------------------------------------
    # STEP 8: Publish & Embed Snippet
    # ----------------------------------------------------
    elif current_step == 8:
        bot_id = st.session_state.get("editing_bot_id")
        bot = client.get_chatbot(bot_id)
        share_details = client.get_share_details(bot_id)

        st.subheader("Step 8: Publish & Share Chatbot")
        st.caption("Manage visibility, public links, and embeddable website integration snippets.")

        is_pub = bot.get("is_published", False) if bot else False
        new_pub_val = st.toggle("Publicly Publish Chatbot", value=is_pub)

        if new_pub_val != is_pub:
            client.set_publish_status(bot_id, new_pub_val)
            st.toast(f"Status changed to {'Published' if new_pub_val else 'Private'}")
            st.rerun()

        if new_pub_val:
            st.success("🎉 Your chatbot is LIVE and publicly accessible via isolated endpoints!")
            pub_url = share_details.get("public_url", "")
            st.markdown(f"**Public Shareable URL:** [Open Chatbot in Browser]({pub_url})")
            st.code(pub_url, language="text")

            st.markdown("#### Embeddable Website Snippet")
            st.caption("Paste this snippet before `</body>` in your website or HTML application to load the chat widget:")
            st.code(share_details.get("embed_code", ""), language="html")
        else:
            st.warning("This chatbot is currently **Private**. Only authorized workspace users can test it in the dashboard.")

        st.markdown("---")
        prev_col, _, finish_col = st.columns([1, 3, 1])
        with prev_col:
            if st.button("⬅️ Back"):
                st.session_state["wizard_step"] = 7
                st.rerun()
        with finish_col:
            if st.button("Go to Dashboard 🏠", type="primary", use_container_width=True):
                st.session_state["nav_selection"] = "Dashboard"
                st.session_state["editing_bot_id"] = None
                st.session_state["wizard_step"] = 1
                st.rerun()

