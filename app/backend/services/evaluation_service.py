from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from app.database.models import Chatbot, EvaluationRun
from app.backend.schemas.evaluation import EvaluationRequest, EvaluationResponse, EvaluationMetricAverages
from app.rag.evaluation.evaluator import RAGEvaluator
from app.rag.retrieval.retriever import RAGRetriever
from app.rag.generation.generator import LLMGenerator


class EvaluationService:
    @staticmethod
    def evaluate_chatbot(
        db: Session,
        chatbot_id: str,
        request: EvaluationRequest
    ) -> EvaluationResponse:
        bot = db.query(Chatbot).filter(Chatbot.id == chatbot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Chatbot not found")

        config = bot.configuration

        # Callable QA pipeline for evaluation runner
        def pipeline_runner(question: str) -> Dict[str, Any]:
            top_k = getattr(config, "top_k", 4) if config else 4
            similarity_threshold = getattr(config, "similarity_threshold", 0.25) if config else 0.25
            embedding_model = getattr(config, "embedding_model", "all-MiniLM-L6-v2") if config else "all-MiniLM-L6-v2"
            
            retrieved = RAGRetriever.retrieve(
                chatbot_id=chatbot_id,
                query=question,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                embedding_model=embedding_model
            )
            return LLMGenerator.generate_response(
                chatbot=bot,
                config=config,
                question=question,
                retrieved_chunks=retrieved
            )

        samples = [s.model_dump() for s in request.samples] if request.samples else None
        report = RAGEvaluator.run_benchmark(pipeline_runner, test_dataset=samples)

        averages = report["averages"]
        run_record = EvaluationRun(
            chatbot_id=chatbot_id,
            test_samples_count=report["samples_evaluated"],
            retrieval_relevance=averages["retrieval_relevance"],
            context_relevance=averages["context_relevance"],
            answer_relevance=averages["answer_relevance"],
            faithfulness=averages["faithfulness"],
            correctness=averages["correctness"],
            detailed_results_json=report["detailed_runs"]
        )
        db.add(run_record)
        db.commit()
        db.refresh(run_record)

        return EvaluationResponse(
            id=run_record.id,
            chatbot_id=chatbot_id,
            methodology_notice=report["methodology_notice"],
            samples_evaluated=report["samples_evaluated"],
            averages=EvaluationMetricAverages(**averages),
            detailed_runs=report["detailed_runs"],
            created_at=run_record.created_at
        )

    @staticmethod
    def get_evaluations(db: Session, chatbot_id: str) -> List[EvaluationRun]:
        return db.query(EvaluationRun).filter(
            EvaluationRun.chatbot_id == chatbot_id
        ).order_by(EvaluationRun.created_at.desc()).all()

