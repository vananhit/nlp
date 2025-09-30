# Bối cảnh kỹ thuật

## Công nghệ Backend

-   **Ngôn ngữ:** Python 3.9+
-   **Framework:** FastAPI
-   **Cơ sở dữ liệu:** SQLite cho sự đơn giản và dễ dàng thiết lập.
-   **Xác thực:** JWT (JSON Web Tokens) để bảo vệ các endpoint.
-   **ORM:** SQLAlchemy để tương tác với cơ sở dữ liệu.
-   **Phụ thuộc chính:**
    -   `fastapi`: Framework web.
    -   `uvicorn`: Máy chủ ASGI.
    -   `sqlalchemy`: ORM.
    -   `python-jose[cryptography]`: Xử lý JWT.
    -   `passlib[bcrypt]`: Băm mật khẩu.
    -   `python-multipart`: Xử lý form data.
    -   `jinja2`: Template engine cho giao diện quản trị.
    -   `google-cloud-aiplatform`: Tích hợp với Google Vertex AI (Gemini).

## Công nghệ Frontend

-   **Giao diện quản trị:** HTML, CSS và JavaScript đơn giản, được render bởi Jinja2.
-   **Ứng dụng khách:** Google Apps Script (`.gs` files), HTML Service (`.html` files).

## Triển khai và Môi trường

-   **Containerization:** Docker và Docker Compose được sử dụng để tạo môi trường phát triển và sản xuất nhất quán.
-   **Biến môi trường:** Cấu hình được quản lý thông qua tệp `.env`.

## Công cụ phát triển

-   **Quản lý gói:** `pip` và `requirements.txt`.
-   **Kiểm soát phiên bản:** Git.
