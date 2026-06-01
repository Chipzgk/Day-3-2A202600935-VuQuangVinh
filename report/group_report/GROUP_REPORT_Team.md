# Báo cáo Nhóm: Lab 3 - Hệ thống Agent cấp độ Thực tiễn (Production-Grade)

- **Team Name**: Kẻ lót đường
- **Team Members**: Vũ Quang Vinh, Hoàng Đức Dũng, Đinh Văn Anh Khôi, Đoàn Công Phú
- **Deployment Date**: 2026-06-01

---

## 1. Tóm tắt Thực thi (Executive Summary)

*Tổng quan về mục tiêu của Agent và tỷ lệ thành công so với Chatbot cơ bản.*

- **Tỷ lệ thành công**: 29.4% độ tin cậy trên 17 kịch bản kiểm thử (Ở phiên bản Baseline v1) -> Đạt 100% thời gian chạy ổn định sau khi áp dụng các rào chắn (Guardrails) ở bản v2.
- **Kết quả chính**: Hệ thống Agent cơ bản đã chứng minh được rằng LLM có khả năng điều phối các công cụ Python cục bộ để tổng hợp ra file vật lý `.wav`. Tuy nhiên, hệ thống cần được áp đặt các rào cản về nhịp độ gửi yêu cầu (throttling) và giới hạn Prompt nghiêm ngặt để "sống sót" qua giới hạn API của Google và ngăn chặn vòng lặp vô hạn.

---

## 2. Kiến trúc Hệ thống & Công cụ

### 2.1 Cấu trúc Vòng lặp ReAct
Hệ thống sử dụng kiến trúc ReAct 5 bước (`max_iterations=5`). LLM đọc ý định người dùng (`Thought`), cấu trúc một tệp JSON để gọi công cụ (`Action`), backend Python thực thi và trả về đường dẫn file (`Observation`), sau đó LLM đóng vòng lặp (`Final Answer`).

### 2.2 Danh mục Công cụ (Tools Inventory)
| Tên Tool | Định dạng Input | Use Case (Mục đích sử dụng) |
| :--- | :--- | :--- |
| `create_midi` | `json` | Tạo file cấu trúc nốt nhạc `.mid` dựa trên nhịp điệu, âm giai và số ô nhịp. |
| `midi_to_wav` | `json` | Bộ kết xuất âm thanh (Synthesizer) đọc file `.mid` và áp dụng sóng âm để xuất audio. |
| `create_music_wav` | `json` | **(Tool đang kích hoạt)** Công cụ All-in-one gộp chung cả bước tạo MIDI và render WAV để giảm số bước suy luận của LLM. |

### 2.3 Các nhà cung cấp LLM
- **Mô hình chính**: `gemini-2.5-flash` (thông qua endpoint `v1beta` của Google AI Studio).
- **Mô hình dự phòng**: Gọi trực tiếp Backend Python (Cơ chế Disaster Recovery khi API sập).

---

## 3. Bảng Phân tích Hiệu năng (Telemetry Dashboard)

*Phân tích các chỉ số công nghiệp thu thập được trong lần chạy kiểm thử.*

- **Độ trễ trung bình (P50)**: 2,939.3 ms mỗi vòng lặp suy luận.
- **Độ trễ tối đa (P99)**: > 23,000 ms (Xảy ra khi thuật toán chống nghẽn Exponential Backoff kích hoạt).
- **Số Token trung bình mỗi tác vụ**: ~235 Prompt Tokens / ~85 Completion Tokens (Tổng: 3,998 Prompt / 1,451 Completion qua 17 lần chạy).
- **Tổng chi phí kiểm thử**: $0.00 (Sử dụng Google Free Tier).

---

## 4. Phân tích Nguyên nhân Gốc rễ (RCA) - Các ca thất bại

### Case Study: Vòng lặp vô hạn (Lỗi Timeout / Max Steps Exceeded)
- **Input**: "Hãy làm cho tôi một đoạn nhạc lofi dài 8 bars, nhịp điệu chậm rãi 80 BPM, tone C."
- **Observation**: Agent gọi thành công `create_music_wav` và hệ thống trả về `Thành công. Kết quả file lưu tại: outputs/lofi_chill.wav`.
- **Nguyên nhân gốc rễ (Root Cause)**: Agent không xuất lệnh `Final Answer`. Do hiện tượng **Trôi dạt ngữ cảnh (Context Drift)** khi lượng token hội thoại tăng lên, LLM quên mất việc phải dừng vòng lặp và tự "ảo giác" ra các tác vụ mới, dẫn đến việc chạm ngưỡng giới hạn số bước.

---

## 5. Nghiên cứu & Thử nghiệm

### Thử nghiệm 1: Prompt v1 so với Prompt v2 (Quy tắc thép)
- **Khác biệt**: Bổ sung rào chắn vào Prompt: *"Nếu Observation có chữ 'Thành công...', BẮT BUỘC KHÔNG gọi tool nữa và phải dùng Final Answer."*
- **Kết quả**: Giảm 100% lỗi lặp vô hạn `Timeout`, đưa hệ thống về trạng thái vận hành Zero-Crash (Không có lỗi crash).

### Thử nghiệm 2 (Điểm thưởng): Chatbot vs Agent
| Phân loại | Câu lệnh (Test Case) | Kết quả Chatbot Baseline | Kết quả ReAct Agent |
| :--- | :--- | :--- | :--- |
| **Chatbot đủ tốt (1)** | *"Vòng hợp âm C - G - Am - F gồm những nốt nào?"* | **Tốt.** Trả lời ngay lập tức bằng văn bản. Tốc độ nhanh, chi phí rẻ. | **Tệ.** Có thể cố gắng dùng tool thừa thãi, tốn thời gian suy nghĩ, tốn token. |
| **Chatbot đủ tốt (2)** | *"Giải thích sự khác nhau giữa nhịp 3/4 và 4/4."* | **Tốt.** Cung cấp kiến thức nhạc lý chuẩn xác trực tiếp. | Trả lời được nhưng tốc độ phản hồi (Latency) chậm hơn do phải đi qua vòng lặp ReAct. |
| **Agent vượt trội (1)** | *"Tạo cho tôi một file âm thanh piano chơi vòng hợp âm C-G-Am-F."* | **Thất bại.** Chỉ nhả ra code, người dùng tay ngang không biết cách dùng. | **Tốt.** Tự phân tích tham số $\rightarrow$ Tự gọi tool `create_music_wav` $\rightarrow$ Trả file âm thanh vật lý. |
| **Agent vượt trội (2)** | *"Tạo file .wav giai điệu bài Twinkle Twinkle Little Star."* | Sinh code dễ bị lỗi logic, user chạy bị lỗi sẽ bỏ cuộc. | **Tốt.** Nếu lúc chạy tool bị lỗi định dạng, Agent tự động đọc Observation, tự sửa lại tham số và chạy lại (Self-correct). |
| **Agent vượt trội (3)** | *"Hãy làm cho tôi một bản nhạc lofi 8 bars, nhịp 80 BPM, tone C."* | **Từ chối.** Xin lỗi vì chỉ là mô hình văn bản (Text-only limit). | **Hoàn hảo.** Nhận diện đúng 100% các biến tham số JSON và kết xuất file `.wav` thành công. |

---

## 6. Đánh giá Mức độ Sẵn sàng Triển khai (Production Readiness)

*Các yếu tố cần cân nhắc khi đưa hệ thống này ra môi trường thực tế.*

- **Bảo mật**: Cần áp dụng xác thực JSON schema (VD: dùng Pydantic) để làm sạch `Action Input` trước khi đưa vào hàm Python cục bộ.
- **Rào chắn (Guardrails)**: Giới hạn cứng `max_iterations=5` và chèn thêm `time.sleep(2.5)` giữa các vòng lặp để tránh làm sập API.
- **Khả năng mở rộng**: Tích hợp bộ định tuyến `SmartRouter` tại cổng kết nối API để phân luồng: Các câu hỏi đơn giản đẩy cho Chatbot, các lệnh phức tạp đẩy cho ReAct Agent nhằm tối ưu chi phí và trải nghiệm người dùng.