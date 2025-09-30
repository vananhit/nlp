# Dự án: Xây dựng "Trợ lý Tái cấu trúc Nội dung SEO"

Tài liệu này tổng hợp bài toán và giải pháp đã được thống nhất để xây dựng một công cụ thông minh hỗ trợ SEOer tối ưu hóa nội dung.

---

## 1. Bài toán (The Problem)

Các SEOer cần một công cụ vượt xa việc kiểm tra lỗi chính tả và ngữ pháp thông thường. Họ cần một trợ lý có khả năng "hiểu" sâu nội dung để đưa ra những cải tiến mang tính chiến lược, giúp bài viết:

- **Tự nhiên và dễ đọc hơn:** Cải thiện trải nghiệm người dùng.
- **Đúng chuẩn E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness):** Nâng cao độ tin cậy và chuyên môn của nội dung.
- **Bám sát Ý định tìm kiếm (Search Intent):** Đáp ứng chính xác điều người dùng mong muốn khi tìm kiếm.
- **Toàn diện về chủ đề:** Đảm bảo không bỏ sót các khía cạnh, khái niệm, hay thực thể quan trọng liên quan đến sản phẩm/chủ đề chính.

---

## 2. Giải pháp (The Solution)

Chúng ta sẽ xây dựng một công cụ tự động có tên là **"Trợ lý Tái cấu trúc Nội dung SEO"**.

Công cụ này kết hợp sức mạnh của hai công nghệ AI hàng đầu:
1.  **Google Natural Language API:** Để phân tích và "bóc tách" nội dung gốc một cách có cấu trúc.
2.  **Mô hình Ngôn ngữ Lớn (LLM):** Để viết lại và tối ưu hóa nội dung dựa trên kết quả phân tích.

---

## 3. Cách hoạt động (How it Works)

Quy trình hoạt động của công cụ bao gồm 2 giai đoạn chính:

### **Đầu vào (User Input)**

Người dùng sẽ cung cấp 3 thông tin đầu vào để định hướng cho AI:
1.  **Nội dung bài viết (Bắt buộc):** Toàn bộ văn bản brouillon cần tối ưu.
2.  **Chủ đề chính (Khuyến khích):** Mô tả ngắn gọn về chủ đề bài viết (ví dụ: "Đánh giá máy ảnh Sony A7IV").
3.  **Ý định tìm kiếm (Khuyến khích):** Mục tiêu của bài viết (ví dụ: "So sánh sản phẩm", "Hướng dẫn cho người mới").

### **Giai đoạn 1: Động cơ Phân tích & Đối chiếu (Analysis & Cross-Reference Engine)**

- **Công nghệ:** Google Natural Language API.
- **Nhiệm vụ:**
    1.  Phân tích nội dung gốc để trích xuất các thông tin quan trọng:
        - **Thực thể (Entities):** Các khái niệm, sản phẩm, thương hiệu chính.
        - **Phân loại (Categories):** Chủ đề của bài viết.
        - **Cú pháp (Syntax):** Các câu văn phức tạp, dài dòng.
        - **Cảm xúc (Sentiment):** Sắc thái, giọng văn của bài viết.
    2.  Đối chiếu kết quả phân tích này với **Chủ đề chính** và **Ý định tìm kiếm** mà người dùng cung cấp để phát hiện sự mâu thuẫn hoặc thiếu sót.
- **Đầu ra:** Một bộ dữ liệu phân tích chi tiết, đã được làm giàu ngữ cảnh.

### **Giai đoạn 2: Động cơ Tái cấu trúc (Refactoring Engine)**

- **Công nghệ:** Một Mô hình Ngôn ngữ Lớn (LLM).
- **Nhiệm vụ:**
    1.  **Tạo Prompt Siêu chi tiết:** Một module tự động sẽ chuyển hóa bộ dữ liệu phân tích từ Giai đoạn 1 thành một mệnh lệnh (prompt) cực kỳ chi tiết và rõ ràng.
    2.  **Viết lại Nội dung:** LLM nhận prompt này và thực hiện việc viết lại toàn bộ nội dung gốc, áp dụng tất cả các yêu cầu về cấu trúc, giọng văn, độ dễ đọc, và sự tập trung vào chủ đề.
- **Đầu ra:** Một phiên bản nội dung hoàn toàn mới, đã được tối ưu hóa theo đúng mục tiêu của người dùng.
