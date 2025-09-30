from google.cloud import language_v2
from backend.services.gcp_sa_manager import gcp_sa_manager

# Việc xác thực giờ đây được quản lý bởi GcpServiceAccountManager.
# Nó sẽ xoay vòng qua các service account có sẵn và cung cấp một client đã được xác thực.

def analyze_text(text_content: str) -> dict:
    """
    Phân tích văn bản bằng Google Cloud Natural Language API.
    Đây là "Động cơ Phân tích" chính của hệ thống.

    Args:
        text_content: Nội dung văn bản cần phân tích.

    Returns:
        Một dictionary chứa kết quả phân tích chi tiết.
    """
    try:
        # Lấy client đã được xác thực từ manager.
        # Manager sẽ xử lý việc xoay vòng qua các service account.
        client = gcp_sa_manager.get_next_client()

        # Tạo một đối tượng Document để gửi đến API.
        document = language_v2.Document(
            content=text_content,
            type_=language_v2.Document.Type.PLAIN_TEXT, # Chỉ định đây là văn bản thuần túy.
            language_code="en" # Có thể để trống để API tự động phát hiện ngôn ngữ.
        )

        # Chỉ định các tính năng phân tích chúng ta muốn API thực hiện bằng cách sử dụng đối tượng Features.
        features = language_v2.AnnotateTextRequest.Features(
            extract_entities=True,
            classify_text=True,
            extract_document_sentiment=True,
        )

        # --- THỰC HIỆN GỌI API ---
        # Gửi yêu cầu phân tích đến Google Cloud.
        # Lưu ý: Tham số `features` được truyền trực tiếp.
        request = language_v2.AnnotateTextRequest(
            document=document,
            features=features,
        )
        response = client.annotate_text(request=request)

        # Xử lý và cấu trúc lại phản hồi từ API thành một dictionary dễ sử dụng hơn.
        results = {
            "entities": [{"name": entity.name, "type": entity.type_.name} for entity in response.entities],
            "categories": [{"name": category.name, "confidence": category.confidence} for category in response.categories],
            "sentiment": {
                "score": response.document_sentiment.score,
                "magnitude": response.document_sentiment.magnitude,
            },
            "language": response.language_code,
        }
        return results

    except Exception as e:
        # Trong một ứng dụng thực tế, bạn sẽ muốn có cơ chế xử lý lỗi và logging tốt hơn.
        print(f"An error occurred with the NLP service: {e}")
        # Ném lại exception để endpoint có thể bắt và trả về lỗi HTTP 500.
        raise e
