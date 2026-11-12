import os
import json
import time
from typing import Dict, Any, List, Optional
from dotenv import find_dotenv, load_dotenv
from app.core.config import settings
from app.core.prompts import PromptBuilder
from app.rag.generation.schema_validator import JSONSchemaValidator


class MockLLMGenerator:
    """
    Synthesizes grounded conversational responses derived from retrieved context
    when no external API key is supplied, ensuring offline testing and demos are seamless.
    """
    @staticmethod
    def generate(
        system_prompt: str,
        user_prompt: str,
        retrieved_chunks: List[Dict[str, Any]],
        fallback_response: str,
        response_format: str,
        json_schema: str = "",
        enable_citations: bool = True,
        question: str = ""
    ) -> str:
        if not retrieved_chunks:
            return fallback_response

        # Top retrieved excerpt
        top_chunk = retrieved_chunks[0]
        meta = top_chunk.get("metadata", {})
        doc_name = meta.get("filename", "document")
        page = meta.get("page_number", 1)
        citation = f"\n\n*(Source: {doc_name}, Page {page})*" if enable_citations else ""

        raw_text = top_chunk.get("content", "").strip()

        # Clean into distinct logical statements
        raw_lines = [
            ln.strip() for ln in raw_text.split("\n")
            if ln.strip() and not ln.startswith("---") and not ln.startswith("Dataset") and not ln.startswith("Dimensions")
        ]
        clean_statements = []
        for line in raw_lines:
            if ":" in line and not line.startswith("http"):
                clean_statements.append(line)
            elif len(line) > 20:
                clean_statements.append(line)

        selected_points = clean_statements[:4] if clean_statements else [raw_text[:250]]

        if response_format == "JSON":
            if json_schema and "answer" in json_schema:
                data = {
                    "answer": " ".join(selected_points[:2]),
                    "confidence": 0.95,
                    "source": f"{doc_name} (Page {page})"
                }
            else:
                data = {
                    "summary": selected_points[0] if selected_points else raw_text[:200],
                    "details": selected_points[1:3],
                    "source_reference": f"{doc_name} (Page {page})",
                    "status": "success"
                }
            return json.dumps(data, indent=2)

        elif response_format == "Bullet Points":
            bullets = [f"• {pt}" for pt in selected_points]
            return (
                "Based on the provided documentation, here are the key findings:\n\n"
                + "\n".join(bullets)
                + citation
            )

        elif response_format == "Numbered Lists":
            nums = [f"{i+1}. {pt}" for i, pt in enumerate(selected_points)]
            return (
                "Based on the provided documentation, here is the step-by-step breakdown:\n\n"
                + "\n".join(nums)
                + citation
            )

        elif response_format == "Tables":
            rows = []
            for i, pt in enumerate(selected_points[:4], 1):
                part1 = f"Point {i}"
                part2 = pt.replace("|", "/")
                if ":" in pt:
                    parts = pt.split(":", 1)
                    part1 = parts[0].strip()
                    part2 = parts[1].strip()
                rows.append(f"| {part1} | {part2} |")
            
            table_body = "\n".join(rows)
            return (
                f"| Specification / Topic | Detail |\n|---|---|\n"
                f"{table_body}\n"
                f"| **Source Reference** | {doc_name} (Page {page}) |"
            )

        else:
            # Paragraphs / Structured Markdown
            joined_content = "\n\n".join([f"• {pt}" for pt in selected_points])
            return (
                f"Based on the verified knowledge base (**{doc_name}**), here is the relevant answer:\n\n"
                f"{joined_content}"
                f"{citation}"
            )


class LLMGenerator:
    @classmethod
    def generate_response(
        cls,
        chatbot: Any,
        config: Any,
        question: str,
        retrieved_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        system_prompt = PromptBuilder.build_system_prompt(config, chatbot)
        user_prompt = PromptBuilder.format_user_prompt_with_context(
            question=question,
            retrieved_chunks=retrieved_chunks,
            conversation_history=conversation_history
        )

        fallback_response = getattr(
            config,
            "fallback_response",
            "I apologize, but I could not find relevant information in the provided knowledge base to answer your question."
        )
        exclusive = getattr(config, "exclusive_knowledge", True)
        response_format = getattr(config, "response_format", "Structured Markdown")
        json_schema = getattr(config, "json_schema", "")
        enable_citations = getattr(config, "enable_citations", True)
        provider = getattr(config, "llm_provider", settings.DEFAULT_LLM_PROVIDER).lower()
        model_name = getattr(config, "llm_model", settings.DEFAULT_LLM_MODEL)

        # If no chunks were retrieved and exclusive knowledge is enforced, return fallback directly
        if not retrieved_chunks and exclusive:
            return {
                "answer": fallback_response,
                "sources": [],
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "provider": "fallback",
                "tokens_used": 0
            }

        answer_text = ""
        used_provider = provider

        # Always check environment and .env dynamically for latest GEMINI_API_KEY
        env_file = find_dotenv(usecwd=True)
        if env_file:
            load_dotenv(env_file, override=True)

        gemini_api_key = os.getenv("GEMINI_API_KEY", "") or getattr(settings, "GEMINI_API_KEY", "")

        # 1. Attempt Google Gemini if provider is gemini and key exists
        if provider == "gemini" and gemini_api_key:
            target_model = model_name or "gemini-1.5-flash"
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=gemini_api_key)
                response = client.models.generate_content(
                    model=target_model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        max_output_tokens=getattr(config, "max_response_tokens", 1024),
                        temperature=0.2
                    )
                )
                answer_text = response.text
                used_provider = f"Google Gemini ({target_model})"
            except Exception as e:
                # If google.genai encounters an error, try google.generativeai fallback
                try:
                    import google.generativeai as gai
                    gai.configure(api_key=gemini_api_key)
                    gmodel = gai.GenerativeModel(
                        model_name=target_model,
                        system_instruction=system_prompt
                    )
                    response = gmodel.generate_content(user_prompt)
                    answer_text = response.text
                    used_provider = f"Google Gemini ({target_model})"
                except Exception as e2:
                    # Fallback to mock and explicitly report error
                    answer_text = MockLLMGenerator.generate(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        retrieved_chunks=retrieved_chunks,
                        fallback_response=fallback_response,
                        response_format=response_format,
                        json_schema=json_schema,
                        enable_citations=enable_citations,
                        question=question
                    )
                    used_provider = f"mock (Gemini Error: {str(e2)[:45]})"

        # 2. Attempt OpenAI if provider is openai and key exists
        elif provider == "openai" and (os.getenv("OPENAI_API_KEY", "") or getattr(settings, "OPENAI_API_KEY", "")):
            openai_key = os.getenv("OPENAI_API_KEY", "") or getattr(settings, "OPENAI_API_KEY", "")
            try:
                from openai import OpenAI
                client = OpenAI(api_key=openai_key)
                response = client.chat.completions.create(
                    model=model_name or "gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=getattr(config, "max_response_tokens", 1024),
                    temperature=0.2
                )
                answer_text = response.choices[0].message.content
                used_provider = f"OpenAI ({model_name or 'gpt-4o-mini'})"
            except Exception as e:
                answer_text = MockLLMGenerator.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    retrieved_chunks=retrieved_chunks,
                    fallback_response=fallback_response,
                    response_format=response_format,
                    json_schema=json_schema,
                    enable_citations=enable_citations,
                    question=question
                )
                used_provider = f"mock (OpenAI Error: {str(e)[:45]})"

        # 3. Default to Grounded Mock LLM Generator (Offline mode)
        else:
            answer_text = MockLLMGenerator.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                retrieved_chunks=retrieved_chunks,
                fallback_response=fallback_response,
                response_format=response_format,
                json_schema=json_schema,
                enable_citations=enable_citations,
                question=question
            )
            used_provider = "offline mock (Add GEMINI_API_KEY to activate live Gemini LLM)"

        # If JSON format requested, validate
        if response_format == "JSON":
            is_valid, err, parsed = JSONSchemaValidator.validate_json_response(answer_text, json_schema)
            if not is_valid:
                fixed = {
                    "raw_response": answer_text,
                    "validation_warning": err,
                    "sources": [c.get("metadata", {}).get("filename") for c in retrieved_chunks]
                }
                answer_text = json.dumps(fixed, indent=2)

        # Prepare source citation metadata
        sources = []
        for chunk in retrieved_chunks:
            meta = chunk.get("metadata", {})
            sources.append({
                "chunk_id": chunk.get("id"),
                "filename": meta.get("filename", "unknown"),
                "page_number": meta.get("page_number", 1),
                "similarity": round(chunk.get("similarity", 0.0), 3),
                "snippet": chunk.get("content", "")[:200]
            })

        latency = round((time.time() - start_time) * 1000, 2)
        token_estimate = len(answer_text.split()) + len(user_prompt.split())

        return {
            "answer": answer_text,
            "sources": sources,
            "latency_ms": latency,
            "provider": used_provider,
            "tokens_used": token_estimate
        }
