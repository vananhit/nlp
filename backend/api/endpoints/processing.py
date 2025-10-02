from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from user_agents import parse

from backend.database import get_db
from backend.models.usage_log import UsageLog
from backend.schemas.token import TokenData
from backend.schemas.content import ContentAnalysisRequest, RewriteResponse
from backend.security import get_current_user
from backend.services import gcp_nlp, llm_rewriter
import pytz
router = APIRouter()

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
    # --- Thu thập thông tin request ---
    user_agent_string = request.headers.get("user-agent", "unknown")
    user_agent = parse(user_agent_string)

    # --- Get real IP from headers ---
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        # The header can contain a comma-separated list of IPs.
        # The client's IP is typically the first one.
        ip_address = x_forwarded_for.split(",")[0].strip()
    else:
        # Fallback to client.host if the header is not present
        ip_address = request.client.host
    
    # --- Ghi log sử dụng ---
    log_entry = UsageLog(
        user_email=x_user_email or "unknown",
        public_ip=ip_address,
        user_agent=user_agent_string,
        browser=user_agent.browser.family,
        browser_version=user_agent.browser.version_string,
        os=user_agent.os.family,
        os_version=user_agent.os.version_string
    )
    db.add(log_entry)
    db.commit()

    # --- GIAI ĐOẠN 1: Động cơ Phân tích & Đối chiếu ---
    analysis_results = gcp_nlp.analyze_text(request_body.content)
    enriched_data = {
        "nlp_analysis": analysis_results,
        "cross_reference_notes": []
    }

    # --- Logic Đối chiếu Nâng cao bằng LLM ---
    llm_analysis_notes = llm_rewriter.analyze_context_with_llm(
        content=request_body.content,
        main_topic=request_body.main_topic,
        search_intent=request_body.search_intent
    )
    enriched_data["cross_reference_notes"].extend(llm_analysis_notes)

    # --- GIAI ĐOẠN 2: Động cơ Tái cấu trúc ---
    rewritten_content = llm_rewriter.rewrite_content_with_gemini(
        enriched_data=enriched_data,
        content=request_body.content
    )

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
