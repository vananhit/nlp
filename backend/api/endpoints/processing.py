from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.usage_log import UsageLog
from backend.schemas.token import TokenData
from backend.schemas.content import ContentAnalysisRequest, RewriteResponse
from backend.security import get_current_user
from backend.services import gcp_nlp, llm_rewriter

router = APIRouter()

@router.post("/process-content", response_model=RewriteResponse)
async def process_content(
    request_body: ContentAnalysisRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_user_email: str | None = Header(default=None, alias="X-User-Email")
) -> RewriteResponse:
    """
    Endpoint được bảo vệ để xử lý nội dung.
    Nhận nội dung, phân tích và trả về phiên bản đã được viết lại.
    """
    try:
        # --- Ghi log sử dụng ---
        log_entry = UsageLog(
            user_email=x_user_email or "unknown",
            request_data=request_body.dict()
        )
        db.add(log_entry)
        db.commit()

        # --- GIAI ĐOẠN 1: Động cơ Phân tích & Đối chiếu ---
        # Gọi service gcp_nlp để thực hiện phân tích sâu nội dung bằng Google NLP API.
        analysis_results = gcp_nlp.analyze_text(request_body.content)

        # Chuẩn bị một dictionary để chứa kết quả phân tích và các ghi chú đối chiếu.
        # Dữ liệu này sẽ được làm giàu và sau đó gửi đến "Động cơ Tái cấu trúc".
        enriched_data = {
            "nlp_analysis": analysis_results,
            "cross_reference_notes": []
        }

        # --- Logic Đối chiếu Nâng cao bằng LLM ---
        # Thay vì so sánh text, chúng ta dùng LLM để "hiểu" và phân tích ngữ nghĩa.
        llm_analysis_notes = llm_rewriter.analyze_context_with_llm(
            content=request_body.content,
            main_topic=request_body.main_topic,
            search_intent=request_body.search_intent
        )
        enriched_data["cross_reference_notes"].extend(llm_analysis_notes)

        # --- GIAI ĐOẠN 2: Động cơ Tái cấu trúc ---
        # Gọi service llm_rewriter, chuyển toàn bộ dữ liệu đã được làm giàu ngữ cảnh
        # để tạo prompt chi tiết và yêu cầu AI viết lại nội dung.
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
    except Exception as e:
        # Bắt các lỗi có thể xảy ra từ các service (ví dụ: lỗi xác thực API của Google).
        # Trong ứng dụng thực tế, nên có logging chi tiết hơn.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during content analysis: {e}"
        )
