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

# --- Schemas for SEO Suggestion Feature ---

class SeoSuggestionRequest(BaseModel):
    keyword: str
    url: Optional[str] = None
    marketing_goal: Optional[str] = None
    target_audience: Optional[str] = None
    brand_voice: Optional[str] = None
    custom_notes: Optional[str] = None
    num_suggestions: int = 3
    output_fields: List[str] = ["title", "description", "h1", "sapo", "content"]

class SeoSuggestion(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    h1: Optional[str] = None
    sapo: Optional[str] = None
    content: Optional[str] = None

class SeoSuggestionResponse(BaseModel):
    suggestions: List[SeoSuggestion]

# --- Schemas for Bio Generation Feature ---

class BioGenerationRequest(BaseModel):
    keyword: str
    website: str
    num_bio_entities: Optional[int] = None
    address: Optional[str] = None
    username: Optional[str] = None
    name: Optional[str] = None
    zipcode: Optional[str] = None
    hotline: Optional[str] = None
    main_keyword: Optional[str] = None
    short_description: Optional[str] = None

class BioGenerationResponse(BaseModel):
    username: str
    name: str
    website: str
    address: str
    zipcode: str
    hotline: str
    hashtag: str
    bioEntities: List[str]
