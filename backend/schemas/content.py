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
    article_type: Optional[str] = None
    url: Optional[str] = None
    marketing_goal: Optional[str] = None
    target_audience: Optional[str] = None
    brand_voice: Optional[str] = None
    language: Optional[str] = "Vietnamese"
    num_suggestions: int = 3
    output_fields: List[str] = ["title", "description", "h1", "sapo", "content"]
    product_info: Optional[str] = None

class CategoryScore(BaseModel):
    name: str
    score: float

class SeoSuggestion(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    h1: Optional[str] = None
    sapo: Optional[str] = None
    content: Optional[str] = None
    categories: Optional[List[CategoryScore]] = None

class SeoSuggestionResponse(BaseModel):
    suggestions: List[SeoSuggestion]

# --- Schemas for SEO Survey Feature ---

class SeoSurveyRequest(BaseModel):
    keyword: str
    name: str
    website: str
    short_description: str
    language: Optional[str] = "Vietnamese"

class SeoSurveyResponse(BaseModel):
    questions: List[str]

# --- Schemas for Bio Survey Feature ---

class BioSurveyRequest(BaseModel):
    keyword: str
    website: Optional[str] = None
    name: Optional[str] = None
    short_description: Optional[str] = None

class BioSurveyResponse(BaseModel):
    questions: List[str]

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
    language: Optional[str] = "Vietnamese"
    entity_context: Optional[str] = None # Tên mới: entity_context

class BioGenerationResponse(BaseModel):
    username: str
    name: str
    website: str
    address: str
    zipcode: str
    hotline: str
    hashtag: str
    bioEntities: List[str]
