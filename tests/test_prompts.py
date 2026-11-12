from app.core.prompts import PromptBuilder


class DummyBot:
    name = "Test Assistant"
    purpose = "Customer support"
    domain = "Customer Support"
    domain_description = ""


class DummyConfig:
    personality = "Friendly"
    tone = "Conversational"
    language = "English"
    response_length = "Short"
    target_audience = "Beginner"
    response_format = "Structured Markdown"
    json_schema = ""
    fallback_response = "Information not found."
    exclusive_knowledge = True
    enable_citations = True
    custom_instructions = "Always offer a follow-up link."
    behavioral_restrictions = "Do not provide investment advice."


def test_build_system_prompt():
    prompt = PromptBuilder.build_system_prompt(DummyConfig(), DummyBot())
    assert "Test Assistant" in prompt
    assert "customer support" in prompt.lower()
    assert "warm, inviting" in prompt
    assert "SECURITY & INJECTION DEFENSE" in prompt
    assert "Always offer a follow-up link." in prompt
    assert "Do not provide investment advice." in prompt


def test_format_user_prompt_with_context():
    chunks = [
        {
            "id": "c1",
            "content": "Returns must be made within 14 days of delivery.",
            "metadata": {"filename": "returns.pdf", "page_number": 3, "chunk_index": 0}
        }
    ]
    formatted = PromptBuilder.format_user_prompt_with_context(
        question="What is the return window?",
        retrieved_chunks=chunks,
        conversation_history=[{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}]
    )

    assert "<UNTRUSTED_KNOWLEDGE_BASE>" in formatted
    assert "returns.pdf" in formatted
    assert "Returns must be made within 14 days" in formatted
    assert "What is the return window?" in formatted
