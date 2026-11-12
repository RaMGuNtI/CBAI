from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.backend.schemas.evaluation import EvaluationRequest, EvaluationResponse
from app.backend.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/chatbots/{chatbot_id}/evaluation", tags=["Evaluation"])


@router.post("", response_model=EvaluationResponse)
def run_evaluation(
    chatbot_id: str,
    request: EvaluationRequest,
    db: Session = Depends(get_db)
):
    return EvaluationService.evaluate_chatbot(db, chatbot_id, request)


@router.get("", response_model=List[dict])
def list_evaluations(
    chatbot_id: str,
    db: Session = Depends(get_db)
):
    runs = EvaluationService.get_evaluations(db, chatbot_id)
    return [
        {
            "id": r.id,
            "chatbot_id": r.chatbot_id,
            "test_samples_count": r.test_samples_count,
            "retrieval_relevance": r.retrieval_relevance,
            "context_relevance": r.context_relevance,
            "answer_relevance": r.answer_relevance,
            "faithfulness": r.faithfulness,
            "correctness": r.correctness,
            "detailed_results": r.detailed_results_json,
            "created_at": r.created_at
        }
        for r in runs
    ]

