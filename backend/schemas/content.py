from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ContentAnalysisRequest(BaseModel):
    content: str
    main_topic: Optional[str] = None
    search_intent: Optional[str] = None

class EnrichedAnalysis(BaseModel):
    nlp_analysis: Dict[str, Any]
    cross_reference_notes: List[str]

class ProcessingResult(BaseModel):
    client_id: str
    enriched_analysis: EnrichedAnalysis

class RewriteResponse(BaseModel):
    client_id: str
    original_content: str
    rewritten_content: str
    analysis_notes: List[str]
