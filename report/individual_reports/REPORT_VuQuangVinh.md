%%writefile report/individual_reports/REPORT_VuQuangVinh.md
# Báo cáo Cá nhân: Lab 3 - Chatbot vs ReAct Agent

- **Họ và Tên**: Vũ Quang Vinh
- **Mã sinh viên**: 2A202600935
- **Ngày nộp**: 01-06-2026

---

## I. Đóng góp Kỹ thuật (15 Điểm)

*Triển khai các rào chắn hệ thống nâng cao, phân loại ý định và cơ chế dự phòng thảm họa API để biến một agent cơ bản mỏng manh thành một hệ thống sẵn sàng cho Production.*

- **Các Module đã triển khai**: `src/core/gemini_provider.py`, `src/agent/agent.py`, `SmartRouter` (Tích hợp UI).
- **Điểm nhấn Mã nguồn**: 
  - Ứng dụng thuật toán **Exponential Backoff** (Lùi bước theo hàm mũ) trong `GeminiProvider` để bẫy các lỗi HTTP 429/503 và chủ động giãn cách thời gian gửi request (sleep 5s -> 10s -> 15s).
  - Xây dựng cơ chế **Disaster Recovery (DR)** bằng khối `try-except` trong `ReActAgent`. Nếu LLM sập hoàn toàn, hệ thống tự động bypass LLM và gọi thẳng công cụ `create_music_wav` với bộ tham số mặc định.
- **Tài liệu hóa**: Thuật toán backoff đảm bảo vòng lặp ReAct không bị văng lỗi giữa chừng khi đối mặt với giới hạn Free Tier của Google (15 RPM). Bộ định tuyến Smart Router đánh giá prompt trước khi vòng lặp bắt đầu, ngăn chặn việc Agent lãng phí token vào các câu hỏi text đơn giản.

---

## II. Nghiên cứu Tình huống Gỡ lỗi (10 Điểm)

*Phân tích một sự cố thất bại cụ thể thông qua hệ thống lưu vết log.*

- **Mô tả Sự cố**: Agent rơi vào vòng lặp vô hạn. Ở vòng 1, nó tạo file âm thanh thành công, nhưng thay vì dừng lại, nó tiếp tục đổi tên file và chạy lại tool cho đến khi chạm mốc `max_iterations=3`, dẫn tới lỗi `Timeout / Max Steps Exceeded` (Xảy ra 7 lần trong 17 phiên test).
- **Nguồn Log**: Telemetry Data (`logs/*.jsonl`) - Độ tin cậy tổng thể: 29.4%.
- **Chẩn đoán**: **Hiện tượng Trôi dạt ngữ cảnh (Context Drift)**. Khi lịch sử hội thoại ReAct dài ra, mô hình `gemini-2.5-flash` mất sự chú ý vào tín hiệu `Observation: Thành công` và quay ngược lại cố gắng giải quyết prompt gốc của người dùng.
- **Giải pháp khắc phục**: Cập nhật `system_prompt` với một **Luật Thép (Strict Constraint)**: *"⚠️ QUY TẮC QUYẾT ĐỊNH: Nếu trong phần 'Observation:' trước đó có chữ 'Thành công. Kết quả file lưu tại...', nhiệm vụ ĐÃ HOÀN THÀNH. Bạn KHÔNG ĐƯỢC gọi thêm công cụ nào nữa. Bạn BẮT BUỘC phải kết luận bằng định dạng: Final Answer:..."*.

---

## III. Góc nhìn Cá nhân: Chatbot vs ReAct (10 Điểm)

*Phản biện về sự khác biệt trong năng lực suy luận.*

1.  **Khả năng Suy luận (Reasoning)**: Khối `Thought` đóng vai trò như một bộ "phiên dịch ngữ nghĩa" xuất sắc. Nó giúp mô hình chia nhỏ một yêu cầu ngôn ngữ tự nhiên mơ hồ ("tạo một beat chill chill") thành một cục JSON chuẩn xác (`{"tempo": 80, "waveform": "lofi", "key": "C"}`) để backend có thể hiểu và chạy được.
2.  **Độ tin cậy (Reliability)**: Thực tế, Agent hoạt động **tệ hơn** Chatbot rất nhiều khi đối mặt với các câu hỏi lý thuyết đơn thuần (VD: "Hợp âm Đô trưởng gồm những nốt nào?"). Nó bị "ảo giác" tự biên dịch code Python để in ra nốt nhạc, làm tăng độ trễ (~3-5 giây) và lãng phí token, trong khi Chatbot có thể trả lời ngay lập tức.
3.  **Tác động của Quan sát (Observation)**: Phản hồi từ môi trường là một con dao hai lưỡi. Dù nó giúp Agent tự sửa sai nếu định dạng JSON bị lỗi, nhưng nếu không có quy tắc dừng nghiêm ngặt, LLM sẽ coi dòng chữ "Thành công" như một đoạn văn bản bình thường chứ không phải là tín hiệu báo kết thúc chương trình.

---

## IV. Hướng Cải tiến Tương lai (5 Điểm)

*Làm thế nào để mở rộng hệ thống này lên mức độ Doanh nghiệp (Production-level)?*

- **Khả năng Mở rộng (Scalability)**: Triển khai một hàng đợi bất đồng bộ (Message Queue như RabbitMQ hoặc Celery) để xử lý các công cụ tốn nhiều thời gian (VD: render file audio dài 3 phút), giúp vòng lặp ReAct không bị kẹt cứng (blocking) trong lúc chờ I/O.
- **An toàn (Safety)**: Tích hợp một LLM "Giám sát" nhẹ (như `gemini-1.5-flash-8b`) để kiểm duyệt chéo các tham số JSON do Agent chính tạo ra trước khi đưa vào môi trường thực thi, nhằm ngăn chặn các mã độc (Prompt Injection).
- **Hiệu năng (Performance)**: Nâng cấp `SmartRouter` từ việc quét từ khóa cơ bản sang một bộ phân loại ý định (Intent Classifier) sử dụng Embedding, giúp điều hướng request chuẩn xác hơn giữa luồng Chatbot, Agent, hoặc quy trình RAG.