from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class CitationSource(BaseModel):
    policy: str
    section: Optional[str] = "General"
    page: Optional[int] = 1
    version: Optional[str] = "1.0"
    score: Optional[float] = 0.0
    text_snippet: Optional[str] = None

class GraderTrace(BaseModel):
    relevance_passed: bool
    relevance_score: float
    answerability_passed: bool
    answerability_score: float
    faithfulness_passed: bool
    faithfulness_score: float
    retry_count: int
    conflict_detected: bool = False
    conflict_details: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    department_filter: Optional[str] = None
    category_filter: Optional[str] = None

class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    answerable: bool
    confidence: float
    sources: List[CitationSource] = []
    trace: Optional[GraderTrace] = None
    latency_ms: float

class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[int]
    title: str
    created_at: datetime
    updated_at: datetime

class FeedbackRequest(BaseModel):
    message_id: str
    rating: int  # 1 or 5
    comment: Optional[str] = None
