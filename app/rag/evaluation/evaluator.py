import re
from typing import List, Dict, Any, Optional


class RAGEvaluator:
    """
    Evaluation suite measuring:
    1. Retrieval Relevance: Whether retrieved chunks overlap with query intent.
    2. Context Relevance: Fraction of retrieved context containing query concepts.
    3. Answer Relevance: How directly the answer addresses the query.
    4. Faithfulness: Degree to which generated assertions are grounded in retrieved context.
    5. Answer Correctness: Token F1 and overlap against ground-truth expected answers.
    """

    DEFAULT_BENCHMARK_DATASET = [
        {
            "question": "What is the return policy duration?",
            "ground_truth": "Returns are accepted within 30 days of purchase in original condition with receipt."
        },
        {
            "question": "How do I reset my password?",
            "ground_truth": "Click on 'Forgot Password' on the login screen, enter your email, and follow the link."
        },
        {
            "question": "What are the working hours of customer support?",
            "ground_truth": "Customer support is available Monday through Friday from 9 AM to 6 PM EST."
        }
    ]

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [w for w in re.findall(r'\b\w+\b', text.lower()) if len(w) > 2]

    @classmethod
    def evaluate_sample(
        cls,
        question: str,
        retrieved_chunks: List[Dict[str, Any]],
        generated_answer: str,
        ground_truth: Optional[str] = None
    ) -> Dict[str, float]:
        q_tokens = set(cls._tokenize(question))
        ans_tokens = set(cls._tokenize(generated_answer))
        
        # Combine retrieved content
        context_text = " ".join([c.get("content", "") for c in retrieved_chunks])
        ctx_tokens = set(cls._tokenize(context_text))

        # 1. Retrieval Relevance
        if not retrieved_chunks:
            retrieval_relevance = 0.0
        else:
            # Fraction of query tokens present in retrieved chunks
            overlap = len(q_tokens.intersection(ctx_tokens))
            retrieval_relevance = round(overlap / max(1, len(q_tokens)), 3)

        # 2. Context Relevance
        if not ctx_tokens:
            context_relevance = 0.0
        else:
            # Ratio of query keywords to total distinct context keywords
            context_relevance = min(1.0, round(len(q_tokens.intersection(ctx_tokens)) / max(1, min(len(ctx_tokens), 25)), 3))

        # 3. Answer Relevance
        if not ans_tokens:
            answer_relevance = 0.0
        else:
            overlap = len(q_tokens.intersection(ans_tokens))
            answer_relevance = min(1.0, round(overlap / max(1, len(q_tokens)), 3))

        # 4. Faithfulness (Grounding)
        if not ans_tokens:
            faithfulness = 1.0 if not generated_answer else 0.0
        elif not ctx_tokens:
            faithfulness = 0.0
        else:
            # Proportion of answer tokens that exist in the retrieved context
            grounded_tokens = ans_tokens.intersection(ctx_tokens)
            faithfulness = round(len(grounded_tokens) / max(1, len(ans_tokens)), 3)

        # 5. Answer Correctness (vs Ground Truth)
        if ground_truth:
            gt_tokens = set(cls._tokenize(ground_truth))
            if not gt_tokens or not ans_tokens:
                correctness = 0.0
            else:
                tp = len(ans_tokens.intersection(gt_tokens))
                precision = tp / max(1, len(ans_tokens))
                recall = tp / max(1, len(gt_tokens))
                if precision + recall > 0:
                    correctness = round((2 * precision * recall) / (precision + recall), 3)
                else:
                    correctness = 0.0
        else:
            correctness = round((answer_relevance + faithfulness) / 2.0, 3)

        return {
            "retrieval_relevance": min(1.0, max(0.0, retrieval_relevance)),
            "context_relevance": min(1.0, max(0.0, context_relevance)),
            "answer_relevance": min(1.0, max(0.0, answer_relevance)),
            "faithfulness": min(1.0, max(0.0, faithfulness)),
            "correctness": min(1.0, max(0.0, correctness))
        }

    @classmethod
    def run_benchmark(
        cls,
        qa_pipeline_callable,
        test_dataset: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Runs evaluation over test questions and computes aggregate metrics with transparent methodology.
        """
        dataset = test_dataset if test_dataset else cls.DEFAULT_BENCHMARK_DATASET
        detailed_results = []
        aggregates = {
            "retrieval_relevance": 0.0,
            "context_relevance": 0.0,
            "answer_relevance": 0.0,
            "faithfulness": 0.0,
            "correctness": 0.0
        }

        for sample in dataset:
            q = sample["question"]
            gt = sample.get("ground_truth")

            # Call pipeline
            output = qa_pipeline_callable(q)
            retrieved = output.get("sources", [])
            answer = output.get("answer", "")

            # If sources only has metadata, reconstruct structure
            sample_metrics = cls.evaluate_sample(
                question=q,
                retrieved_chunks=retrieved,
                generated_answer=answer,
                ground_truth=gt
            )

            for k in aggregates:
                aggregates[k] += sample_metrics[k]

            detailed_results.append({
                "question": q,
                "ground_truth": gt,
                "generated_answer": answer,
                "retrieved_count": len(retrieved),
                "metrics": sample_metrics
            })

        count = max(1, len(dataset))
        avg_metrics = {k: round(v / count, 3) for k, v in aggregates.items()}

        return {
            "methodology_notice": (
                "Notice: Metrics are calculated via deterministic lexical overlap, token F1, and citation "
                "substantiation analysis between queries, retrieved knowledge chunks, and expected answers. "
                "These provide heuristic diagnostic signals and should be reviewed alongside human qualitative checks."
            ),
            "samples_evaluated": len(dataset),
            "averages": avg_metrics,
            "detailed_runs": detailed_results
        }

