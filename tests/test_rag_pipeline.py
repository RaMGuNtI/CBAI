import pytest
from app.rag.chunking.chunker import DocumentChunk
from app.rag.vector_store.chroma_manager import ChromaManager
from app.rag.retrieval.retriever import RAGRetriever, BM25KeywordRanker
from app.rag.generation.schema_validator import JSONSchemaValidator
from app.rag.evaluation.evaluator import RAGEvaluator


def test_bm25_keyword_ranker():
    query = "return policy warranty"
    doc1 = "Our return policy allows items to be returned within 30 days under full warranty."
    doc2 = "The sky is blue and the sun is shining."

    score1 = BM25KeywordRanker.score(query, doc1)
    score2 = BM25KeywordRanker.score(query, doc2)

    assert score1 > score2
    assert score2 == 0.0


def test_json_schema_validator():
    schema = '{"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}'
    valid_json = '{"name": "CustomBot"}'
    invalid_json = '{"age": 25}'
    broken_syntax = '{"name": '

    is_v, err, _ = JSONSchemaValidator.validate_json_response(valid_json, schema)
    assert is_v is True

    is_inv, err_inv, _ = JSONSchemaValidator.validate_json_response(invalid_json, schema)
    assert is_inv is False
    assert "required" in err_inv.lower()

    is_brk, err_brk, _ = JSONSchemaValidator.validate_json_response(broken_syntax, schema)
    assert is_brk is False
    assert "invalid json" in err_brk.lower()


def test_rag_evaluator_metrics():
    q = "What is the warranty period?"
    chunks = [{"content": "All equipment comes with a standard 2-year warranty covering manufacturing defects."}]
    ans = "The standard warranty period is 2 years covering defects."
    gt = "2 years warranty period."

    metrics = RAGEvaluator.evaluate_sample(
        question=q,
        retrieved_chunks=chunks,
        generated_answer=ans,
        ground_truth=gt
    )

    assert metrics["retrieval_relevance"] > 0.0
    assert metrics["faithfulness"] > 0.0
    assert metrics["correctness"] > 0.0


def test_chroma_isolated_indexing_and_retrieval():
    bot_id = "test_bot_iso_123"
    chunk = DocumentChunk(
        id="chunk_1",
        chatbot_id=bot_id,
        document_id="doc_1",
        filename="test.txt",
        page_number=1,
        chunk_index=0,
        content="Alpha protocol requires emergency shutdown within 10 seconds of alarm.",
        metadata={"filename": "test.txt", "chatbot_id": bot_id, "document_id": "doc_1"}
    )

    # Clean prior collection if any
    ChromaManager.delete_chatbot_collection(bot_id)

    # Add chunk
    added = ChromaManager.add_chunks(bot_id, [chunk])
    assert added == 1

    # Query
    results = RAGRetriever.retrieve(
        chatbot_id=bot_id,
        query="emergency shutdown protocol",
        top_k=2,
        similarity_threshold=0.1
    )

    assert len(results) >= 1
    assert "Alpha protocol" in results[0]["content"]

    # Clean up
    ChromaManager.delete_chatbot_collection(bot_id)

