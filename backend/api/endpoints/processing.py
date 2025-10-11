from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from user_agents import parse

from backend.database import get_db
from backend.models.usage_log import UsageLog
from backend.schemas.token import TokenData
from backend.schemas.content import (
    ContentAnalysisRequest, 
    RewriteResponse,
    SeoSuggestionRequest,
    SeoSuggestionResponse,
    SeoSuggestion,
    BioGenerationRequest,
    BioGenerationResponse
)
from backend.security import get_current_user
from backend.services import gcp_nlp, llm_rewriter
from backend.core import seo_workflow, bio_workflow
from langgraph.graph import StateGraph, END
import pytz

router = APIRouter()

def _log_usage(db: Session, request: Request, user_email: str | None, feature_name: str):
    """Hàm trợ giúp để ghi log sử dụng tính năng."""
    user_agent_string = request.headers.get("user-agent", "unknown")
    user_agent = parse(user_agent_string)

    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(",")[0].strip()
    else:
        ip_address = request.client.host

    log_entry = UsageLog(
        user_email=user_email or "unknown",
        public_ip=ip_address,
        user_agent=user_agent_string,
        browser=user_agent.browser.family,
        browser_version=user_agent.browser.version_string,
        os=user_agent.os.family,
        os_version=user_agent.os.version_string,
        feature_name=feature_name
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

def process_content_sync(
    db: Session,
    request_body: ContentAnalysisRequest,
    current_user: TokenData,
    x_user_email: str | None,
    request: Request
) -> RewriteResponse:
    """
    Hàm đồng bộ chứa logic xử lý nội dung nặng.
    Hàm này sẽ được chạy trong một thread riêng để không block event loop.
    """
    # --- Ghi log sử dụng ---
    _log_usage(db, request, x_user_email, "Viết lại nội dung")

    # --- GIAI ĐOẠN 1: Động cơ Phân tích & Đối chiếu ---
    analysis_results = gcp_nlp.analyze_text(request_body.content)
    enriched_data = {
        "nlp_analysis": analysis_results,
        "cross_reference_notes": []
    }

    # --- Logic Đối chiếu Nâng cao bằng LLM (Async Wrapper) ---
    async def async_tasks():
        llm_analysis_task = llm_rewriter.analyze_context_with_llm(
            content=request_body.content,
            main_topic=request_body.main_topic,
            search_intent=request_body.search_intent
        )
        
        # For now, we run this sequentially. Can be run in parallel if needed.
        llm_analysis_notes = await llm_analysis_task
        enriched_data["cross_reference_notes"].extend(llm_analysis_notes)

        # --- GIAI ĐOẠN 2: Động cơ Tái cấu trúc ---
        rewritten_content = await llm_rewriter.rewrite_content_with_gemini(
            enriched_data=enriched_data,
            content=request_body.content
        )
        return rewritten_content

    # Since process_content_sync is a sync function run in a threadpool,
    # we can create a new event loop to run our async functions.
    import asyncio
    rewritten_content = asyncio.run(async_tasks())

    # Trả về kết quả cho client theo cấu trúc của schema RewriteResponse.
    return RewriteResponse(
        client_id=current_user.username,
        original_content=request_body.content,
        rewritten_content=rewritten_content,
        analysis_notes=enriched_data["cross_reference_notes"]
    )

@router.post("/process-content", response_model=RewriteResponse)
async def process_content(
    request_body: ContentAnalysisRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_user_email: str | None = Header(default=None, alias="X-User-Email")
) -> RewriteResponse:
    """
    Endpoint được bảo vệ để xử lý nội dung.
    Nhận nội dung, phân tích và trả về phiên bản đã được viết lại.
    Các tác vụ blocking sẽ được chạy trong một thread pool riêng.
    """
    try:
        # Chạy hàm xử lý đồng bộ trong một thread riêng
        response = await run_in_threadpool(
            process_content_sync,
            db=db,
            request_body=request_body,
            current_user=current_user,
            x_user_email=x_user_email,
            request=request
        )
        return response
    except Exception as e:
        # Bắt các lỗi có thể xảy ra từ các service (ví dụ: lỗi xác thực API của Google).
        # Trong ứng dụng thực tế, nên có logging chi tiết hơn.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during content analysis: {e}"
        )

@router.post("/generate-seo-suggestions", response_model=SeoSuggestionResponse)
async def generate_seo_suggestions(
    request_body: SeoSuggestionRequest,
    request: Request,
    db: Session = Depends(get_db),
    x_user_email: str | None = Header(default=None, alias="X-User-Email")
) -> SeoSuggestionResponse:
    """
    Endpoint để tạo gợi ý nội dung SEO dựa trên từ khóa.
    Sử dụng LangGraph để điều phối một workflow phức tạp:
    1. Crawl top 10 Google results.
    2. Analyze each result using GCP NLP and a custom LLM analyzer.
    3. Synthesize insights into a master content brief.
    4. Generate multiple content suggestions based on the brief.
    """
    # --- Ghi log sử dụng ---
    _log_usage(db, request, x_user_email, "Gợi ý SEO")
    
    # --- 1. Xây dựng Graph Workflow ---
    workflow = StateGraph(seo_workflow.GraphState)

    # Thêm các node vào graph theo workflow mới
    workflow.add_node("fetch_articles", seo_workflow.fetch_top_articles)
    workflow.add_node("analyze_content", seo_workflow.analyze_articles)
    workflow.add_node("synthesize", seo_workflow.synthesize_analysis)
    workflow.add_node("generate_ideas", seo_workflow.generate_initial_ideas)
    workflow.add_node("generate_outlines", seo_workflow.generate_outlines)
    workflow.add_node("generate_articles", seo_workflow.generate_full_articles)

    # Kết nối các node theo đúng thứ tự
    workflow.set_entry_point("fetch_articles")
    workflow.add_edge("fetch_articles", "analyze_content")
    workflow.add_edge("analyze_content", "synthesize")
    workflow.add_edge("synthesize", "generate_ideas")
    workflow.add_edge("generate_ideas", "generate_outlines")
    workflow.add_edge("generate_outlines", "generate_articles")
    workflow.add_edge("generate_articles", END)

    # Compile graph thành một đối tượng có thể thực thi
    app = workflow.compile()

    # --- 2. Chuẩn bị đầu vào và thực thi Graph ---
    initial_state = {
        "keyword": request_body.keyword,
        "output_fields": request_body.output_fields,
        "num_suggestions": request_body.num_suggestions,
        "language": request_body.language,
        "article_type": request_body.article_type,
        # --- Lấy ngữ cảnh từ request ---
        "marketing_goal": request_body.marketing_goal,
        "target_audience": request_body.target_audience,
        "brand_voice": request_body.brand_voice,
        "custom_notes": request_body.custom_notes,
        # Các trường khác sẽ được điền bởi các node
        "top_articles": [],
        "analysis_results": [],
        "content_brief": "",
        "seo_ideas": [],
        "outlines": [],
        "final_suggestions": []
    }

    try:
        # Chạy workflow bất đồng bộ
        final_state = await app.ainvoke(initial_state)
        
        # --- 3. Định dạng và trả về kết quả ---
        # Chuyển đổi kết quả từ dict sang Pydantic model
        suggestions_list = [SeoSuggestion(**s) for s in final_state.get('final_suggestions', [])]
        
        return SeoSuggestionResponse(suggestions=suggestions_list)

    except Exception as e:
        # Xử lý lỗi chung từ workflow
        # Trong thực tế, nên có logging chi tiết hơn
        print(f"Error during SEO suggestion workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred in the SEO suggestion workflow: {e}"
        )

@router.post("/generate-bio-entities", response_model=BioGenerationResponse)
async def generate_bio_entities(
    request_body: BioGenerationRequest,
    request: Request,
    db: Session = Depends(get_db),
    x_user_email: str | None = Header(default=None, alias="X-User-Email")
) -> BioGenerationResponse:
    """
    Endpoint to generate bio entities based on provided keywords and information.
    Uses a LangGraph workflow to orchestrate LLM calls for generating:
    1. Basic company/entity info if missing.
    2. Relevant hashtags.
    3. A list of bio paragraphs.
    """
    # --- Ghi log sử dụng ---
    _log_usage(db, request, x_user_email, "Tạo Bio")

    # --- 1. Build Workflow Graph ---
    workflow = StateGraph(bio_workflow.BioGraphState)

    # Add nodes to the graph
    workflow.add_node("generate_info", bio_workflow.generate_basic_info)
    workflow.add_node("generate_hashtags", bio_workflow.generate_hashtags)
    workflow.add_node("generate_bios", bio_workflow.generate_bio_entities)

    # Connect the nodes in sequence
    workflow.set_entry_point("generate_info")
    workflow.add_edge("generate_info", "generate_hashtags")
    workflow.add_edge("generate_hashtags", "generate_bios")
    workflow.add_edge("generate_bios", END)

    # Compile the graph
    app = workflow.compile()

    # --- 2. Prepare Initial State and Invoke Graph ---
    initial_state = request_body.dict()
    
    # Ensure keys for populated fields exist
    initial_state.setdefault("hashtag", None)
    initial_state.setdefault("bioEntities", None)


    try:
        # Asynchronously invoke the workflow
        final_state = await app.ainvoke(initial_state)
        
        # --- 3. Format and Return Response ---
        # The final state should match the BioGenerationResponse schema
        return BioGenerationResponse(**final_state)

    except Exception as e:
        print(f"Error during bio generation workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred in the bio generation workflow: {e}"
        )
