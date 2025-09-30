# Project Brief: SEO Tool NLP Backend

## Tổng quan

Dự án này là một backend cho công cụ SEO, tập trung vào việc cung cấp các dịch vụ xử lý ngôn ngữ tự nhiên (NLP). Hệ thống được xây dựng bằng Python với framework FastAPI và bao gồm các thành phần để quản lý xác thực, khách hàng, khóa API và xử lý nội dung.

## Mục tiêu chính

1.  **Cung cấp API NLP:** Xây dựng các endpoint API mạnh mẽ để xử lý và phân tích văn bản cho mục đích SEO.
2.  **Quản lý người dùng và khách hàng:** Triển khai hệ thống xác thực an toàn và giao diện quản trị để quản lý các ứng dụng khách, khóa API và tài khoản dịch vụ GCP.
3.  **Ghi lại và giám sát:** Theo dõi việc sử dụng API để phân tích và thanh toán.
4.  **Tích hợp LLM:** Tích hợp với các mô hình ngôn ngữ lớn (LLM) như Gemini để viết lại và tối ưu hóa nội dung.
5.  **Giao diện người dùng:** Cung cấp giao diện quản trị đơn giản để quản lý hệ thống và xem lịch sử sử dụng.

## Phạm vi

-   **Backend:** API được xây dựng bằng FastAPI, cơ sở dữ liệu SQLite, xác thực JWT.
-   **Frontend (Quản trị):** Giao diện quản trị cơ bản sử dụng Jinja2 templates.
-   **Frontend (Khách hàng):** Một ứng dụng Google Apps Script (`Code.gs`, `Sidebar.html`) tương tác với backend.
-   **Triển khai:** Docker được sử dụng để đóng gói và triển khai ứng dụng.
