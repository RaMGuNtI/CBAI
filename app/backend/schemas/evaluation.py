from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class BenchmarkSample(BaseModel):
    question: str
    ground_truth: Optional[str] = None


class EvaluationRequest(BaseModel):
    samples: Optional[List[BenchmarkSample]] = None


class EvaluationMetricAverages(BaseModel):
    retrieval_relevance: float
    context_relevance: float
    answer_relevance: float
    faithfulness: float
    correctness: float


class EvaluationResponse(BaseModel):
    id: Optional[str] = None
    chatbot_id: str
    methodology_notice: str
    samples_evaluated: int
    averages: EvaluationMetricAverages
    detailed_runs: List[Dict[str, Any]]
    created_at: Optional[datetime] = None

