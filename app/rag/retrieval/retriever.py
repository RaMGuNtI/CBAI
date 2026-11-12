import math
import re
from typing import List, Dict, Any, Optional
from app.rag.vector_store.chroma_manager import ChromaManager


class BM25KeywordRanker:
    """
    Lightweight BM25 lexical ranker for hybrid search.
    """
    @staticmethod
    def tokenize(text: str) -> List[str]:
        return re.findall(r'\b\w+\b', text.lower())

    @classmethod
    def score(cls, query: str, document: str) -> float:
        q_tokens = cls.tokenize(query)
        doc_tokens = cls.tokenize(document)
        if not q_tokens or not doc_tokens:
            return 0.0

        doc_len = len(doc_tokens)
        doc_counts = {}
        for t in doc_tokens:
            doc_counts[t] = doc_counts.get(t, 0) + 1

        k1 = 1.5
        b = 0.75
        avg_len = 100.0

        score = 0.0
        for token in q_tokens:
            if token in doc_counts:
                tf = doc_counts[token]
                term_score = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_len)))
                score += term_score

        return score


class RAGRetriever:
    """
    Orchestrates vector search, similarity threshold filtering, hybrid keyword combination,
    and reranking.
    """

    @classmethod
    def retrieve(
        cls,
        chatbot_id: str,
        query: str,
        top_k: int = 4,
        similarity_threshold: float = 0.25,
        retrieval_strategy: str = "similarity",
        enable_hybrid: bool = False,
        enable_reranking: bool = False,
        embedding_model: str = "all-MiniLM-L6-v2"
    ) -> List[Dict[str, Any]]:
        # 1. Fetch dense candidates from ChromaDB (retrieve 2x if reranking or hybrid is enabled)
        candidate_k = top_k * 2 if (enable_hybrid or enable_reranking) else top_k
        candidates = ChromaManager.query(
            chatbot_id=chatbot_id,
            query_text=query,
            top_k=candidate_k,
            embedding_model_name=embedding_model
        )

        if not candidates:
            return []

        # 2. Hybrid Lexical Scoring (BM25)
        if enable_hybrid:
            for item in candidates:
                bm25_score = BM25KeywordRanker.score(query, item["content"])
                # Normalize bm25 and fuse with cosine similarity: 70% dense + 30% lexical
                dense_score = item["similarity"]
                lexical_score = min(1.0, bm25_score / 5.0)
                item["similarity"] = (0.7 * dense_score) + (0.3 * lexical_score)
                item["bm25_score"] = bm25_score

        # 3. Apply retrieval strategy
        if retrieval_strategy == "threshold":
            filtered = [item for item in candidates if item["similarity"] >= similarity_threshold]
            candidates = filtered if filtered else []
        elif retrieval_strategy == "mmr":
            # Maximal Marginal Relevance approximation
            candidates = cls._apply_mmr(candidates, top_k)
        else:
            # Default similarity ranking
            candidates = sorted(candidates, key=lambda x: x["similarity"], reverse=True)

        # 4. Reranking (Cross-matching term density and structural relevance)
        if enable_reranking and candidates:
            candidates = cls._apply_reranker(query, candidates)

        # 5. Apply threshold floor to prevent irrelevant noise
        final_candidates = [
            c for c in candidates if c["similarity"] >= similarity_threshold
        ][:top_k]

        return final_candidates

    @classmethod
    def _apply_mmr(cls, candidates: List[Dict[str, Any]], top_k: int, lambda_param: float = 0.6) -> List[Dict[str, Any]]:
        """
        Simple greedy MMR selection to maximize relevance while penalizing redundancy.
        """
        if len(candidates) <= top_k:
            return candidates

        selected: List[Dict[str, Any]] = []
        remaining = list(candidates)

        while remaining and len(selected) < top_k:
            best_item = None
            best_mmr_score = -float("inf")

            for item in remaining:
                relevance = item["similarity"]
                if not selected:
                    redundancy = 0.0
                else:
                    # Measure word overlap with already selected items
                    item_words = set(BM25KeywordRanker.tokenize(item["content"]))
                    redundancies = [
                        len(item_words.intersection(set(BM25KeywordRanker.tokenize(s["content"])))) / (len(item_words) + 1e-5)
                        for s in selected
                    ]
                    redundancy = max(redundancies) if redundancies else 0.0

                mmr_score = (lambda_param * relevance) - ((1.0 - lambda_param) * redundancy)
                if mmr_score > best_mmr_score:
                    best_mmr_score = mmr_score
                    best_item = item

            if best_item:
                selected.append(best_item)
                remaining.remove(best_item)
            else:
                break

        return selected

    @classmethod
    def _apply_reranker(cls, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Reranker that boosts items with exact keyword matches, title matches, and query term density.
        """
        q_tokens = set(BM25KeywordRanker.tokenize(query))
        
        for item in candidates:
            content_lower = item["content"].lower()
            exact_match_boost = 0.15 if query.lower() in content_lower else 0.0
            
            # Match in filename or metadata
            filename = item.get("metadata", {}).get("filename", "").lower()
            filename_boost = 0.1 if any(t in filename for t in q_tokens if len(t) > 3) else 0.0

            item["similarity"] = min(1.0, item["similarity"] + exact_match_boost + filename_boost)

        return sorted(candidates, key=lambda x: x["similarity"], reverse=True)

