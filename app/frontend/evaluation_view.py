import streamlit as st
import pandas as pd
from app.frontend.components.api_client import client
from app.frontend.components.ui import render_metric_card


def render_evaluation_view():
    st.markdown('<div class="main-header">🎯 RAG Evaluation & Diagnostics</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-sub">Quantify retrieval precision, context relevance, faithfulness, and answer correctness.</div>', unsafe_allow_html=True)

    bots = client.list_chatbots()
    if not bots:
        st.info("No chatbots available to evaluate.")
        return

    bot_options = {b["id"]: f"{b.get('bot_avatar', '🤖')} {b['name']}" for b in bots}
    active_bot_id = st.session_state.get("active_bot_id")
    if not active_bot_id or active_bot_id not in bot_options:
        active_bot_id = list(bot_options.keys())[0]

    selected_bot_id = st.selectbox(
        "Select Chatbot to Evaluate",
        options=list(bot_options.keys()),
        format_func=lambda x: bot_options[x],
        index=list(bot_options.keys()).index(active_bot_id)
    )

    st.markdown(f"""
        <div class="callout-box">
            <b>Evaluation Methodology Transparency:</b><br/>
            CustomBot AI computes heuristic metrics using lexical overlap, token F1 scores, citation substantiation, 
            and context alignment. These metrics serve as relative diagnostic benchmarks for tuning chunk sizes and retrieval 
            parameters, and should not be treated as infallible objective ground truth.
        </div>
    """, unsafe_allow_html=True)

    st.subheader("Test Dataset Configuration")
    st.caption("Provide benchmark questions and expected ground-truth answers for your knowledge base.")

    default_test_cases = [
        {"question": "What is the return policy duration?", "ground_truth": "Returns are accepted within 30 days."},
        {"question": "How do I contact customer support?", "ground_truth": "Contact support via email or phone 9 AM to 6 PM."},
        {"question": "What documents are required for verification?", "ground_truth": "Government photo ID and address proof."}
    ]

    use_custom_tests = st.checkbox("Define custom test questions", value=False)
    test_samples = None

    if use_custom_tests:
        sample_q1 = st.text_input("Question 1", value="What is the primary topic of the document?")
        sample_gt1 = st.text_input("Expected Answer 1", value="Overview of company policies.")
        test_samples = [{"question": sample_q1, "ground_truth": sample_gt1}]
    else:
        st.write("Using default benchmark questions (3 test samples).")

    if st.button("🚀 Run RAG Benchmark", type="primary"):
        with st.spinner("Executing retrieval queries, measuring ground-truth alignment, and computing scores..."):
            eval_report = client.run_evaluation(selected_bot_id, test_samples=test_samples)
            if eval_report:
                st.session_state[f"last_eval_{selected_bot_id}"] = eval_report
                st.success("Benchmark completed successfully!")
            else:
                st.error("Evaluation run failed. Please check backend logs.")

    last_eval = st.session_state.get(f"last_eval_{selected_bot_id}")
    if last_eval:
        st.markdown("---")
        st.subheader("Benchmark Results Summary")

        avgs = last_eval.get("averages", {})
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            render_metric_card("Retrieval Rel.", f"{avgs.get('retrieval_relevance', 0.0) * 100:.1f}%", icon="🎯")
        with c2:
            render_metric_card("Context Rel.", f"{avgs.get('context_relevance', 0.0) * 100:.1f}%", icon="🔍")
        with c3:
            render_metric_card("Answer Rel.", f"{avgs.get('answer_relevance', 0.0) * 100:.1f}%", icon="💬")
        with c4:
            render_metric_card("Faithfulness", f"{avgs.get('faithfulness', 0.0) * 100:.1f}%", icon="🛡️")
        with c5:
            render_metric_card("Correctness", f"{avgs.get('correctness', 0.0) * 100:.1f}%", icon="✅")

        # Visual chart
        chart_data = pd.DataFrame({
            "Metric": ["Retrieval Relevance", "Context Relevance", "Answer Relevance", "Faithfulness", "Correctness"],
            "Score": [
                avgs.get("retrieval_relevance", 0.0),
                avgs.get("context_relevance", 0.0),
                avgs.get("answer_relevance", 0.0),
                avgs.get("faithfulness", 0.0),
                avgs.get("correctness", 0.0)
            ]
        })
        st.bar_chart(chart_data.set_index("Metric"))

        st.subheader("Question-by-Question Breakdown")
        for item in last_eval.get("detailed_runs", []):
            with st.expander(f"Q: {item.get('question')}", expanded=True):
                st.markdown(f"**Expected Answer:** {item.get('ground_truth', 'N/A')}")
                st.markdown(f"**Generated Answer:** {item.get('generated_answer')}")
                m = item.get("metrics", {})
                st.caption(
                    f"Retrieval: {m.get('retrieval_relevance', 0):.2f} | "
                    f"Context: {m.get('context_relevance', 0):.2f} | "
                    f"Answer Rel: {m.get('answer_relevance', 0):.2f} | "
                    f"Faithfulness: {m.get('faithfulness', 0):.2f} | "
                    f"Correctness: {m.get('correctness', 0):.2f}"
                )

