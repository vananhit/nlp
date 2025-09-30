# Các mẫu hệ thống

## Kiến trúc tổng thể

Hệ thống được thiết kế theo kiến trúc client-server.

-   **Server (Backend):** Một ứng dụng FastAPI cung cấp các API RESTful để xử lý logic nghiệp vụ, tương tác với cơ sở dữ liệu và tích hợp với các dịch vụ của bên thứ ba (Google Cloud NLP, Gemini).
-   **Client (Frontend):**
    -   Một giao diện quản trị dựa trên web được tạo bằng Jinja2 templates để quản lý hệ thống.
    -   Một ứng dụng Google Apps Script hoạt động như một ứng dụng khách chính, gọi đến các API của backend.

## Các mẫu thiết kế Backend

-   **Repository Pattern:** Logic truy cập dữ liệu được trừu tượng hóa bằng cách sử dụng các hàm trong `database.py` và các mô hình SQLAlchemy, mặc dù không được triển khai một cách nghiêm ngặt như một lớp repository riêng biệt.
-   **Dependency Injection:** FastAPI sử dụng cơ chế dependency injection một cách rộng rãi để quản lý các phụ thuộc như session cơ sở dữ liệu (`get_db`) và xác thực người dùng (`get_current_active_user`).
-   **Layered Architecture (Kiến trúc phân lớp):**
    -   **Lớp API (Endpoints):** Xử lý các yêu cầu HTTP, xác thực đầu vào và gọi đến lớp dịch vụ. Nằm trong `backend/api/endpoints/`.
    -   **Lớp dịch vụ (Services):** Chứa logic nghiệp vụ chính của ứng dụng. Ví dụ: `gcp_nlp.py`, `llm_rewriter.py`.
    -   **Lớp dữ liệu (Data Access):** Bao gồm các mô hình SQLAlchemy (`backend/models/`) và logic tương tác cơ sở dữ liệu (`backend/database.py`).
-   **Configuration Management:** Cấu hình được quản lý tập trung thông qua `backend/core/config.py`, đọc các giá trị từ biến môi trường.

## Mẫu xác thực và bảo mật

-   **OAuth2 với Password Flow và JWT:** Xác thực người dùng được xử lý thông qua endpoint `/token` sử dụng OAuth2 password flow. Sau khi xác thực thành công, một JWT access token được cấp cho client.
-   **API Key Authentication:** Các ứng dụng khách (ví dụ: Google Apps Script) xác thực với backend bằng cách sử dụng một khóa API duy nhất được truyền trong header `X-API-KEY`.
-   **Password Hashing:** Mật khẩu người dùng được băm bằng bcrypt trước khi lưu vào cơ sở dữ liệu.
