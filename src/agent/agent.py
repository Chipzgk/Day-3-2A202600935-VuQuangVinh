import re
import json
import os
import time
from src.utils.telemetry import logger
from src.core.gemini_provider import GeminiProvider
from src.tools.music_tools import create_music_wav

class ReActAgent:
    # NÂNG CẤP: Nới rộng max_iterations lên 5 vòng lặp để chống lỗi Timeout
    def __init__(self, max_iterations=5):
        api_key = os.getenv("GEMINI_API_KEY")
        self.provider = GeminiProvider(model_name="gemini-2.5-flash", api_key=api_key)
        self.max_iterations = max_iterations
        self.tools_map = {"create_music_wav": create_music_wav}
        
        self.system_prompt = """
        Bạn là một AI Music Agent. Nhiệm vụ của bạn là giải quyết yêu cầu của người dùng.
        Bạn có công cụ sau:
        1. create_music_wav: Tạo thẳng file .wav (Input: {"title": str, "mood": str, "key": str, "tempo": int, "bars": int, "waveform": str})

        BẮT BUỘC phản hồi theo định dạng chính xác sau:
        Thought: Suy nghĩ của bạn.
        Action: create_music_wav
        Action Input: CHUỖI JSON HỢP LỆ.
        
        ⚠️ QUY TẮC QUYẾT ĐỊNH:
        Nếu trong phần 'Observation:' trước đó có chữ 'Thành công. Kết quả file lưu tại...', nhiệm vụ ĐÃ HOÀN THÀNH. Bạn KHÔNG ĐƯỢC gọi thêm công cụ nào nữa. Bạn BẮT BUỘC phải kết luận bằng định dạng sau để đóng luồng:
        Final Answer: Tôi đã tạo thành công file nhạc theo yêu cầu của bạn tại [Đường dẫn file].
        """

    def run(self, user_prompt: str):
        logger.log_event("Agent_Start", "User_Prompt", user_prompt)
        conversation_history = f"User: {user_prompt}\n"
        
        for i in range(1, self.max_iterations + 1):
            print(f"\n--- Vòng lặp Live {i} ---")
            if i > 1:
                time.sleep(1.5) # Giảm khoảng nghỉ giữa các vòng
                
            response_data = self.provider.generate(conversation_history, self.system_prompt)
            response_text = response_data["content"]
            metrics = {"usage": response_data["usage"], "latency_ms": response_data["latency_ms"]}
            
            logger.log_event(f"Iteration_{i}", "LLM_Response", response_text, metadata=metrics)

            if "Final Answer:" in response_text:
                final_answer = response_text.split("Final Answer:")[-1].strip()
                logger.log_event(f"Iteration_{i}", "Final_Answer", final_answer)
                return final_answer

            action_match = re.search(r"Action:\s*(.*)", response_text)
            input_match = re.search(r"Action Input:\s*(.*)", response_text, re.DOTALL)
            
            if not action_match or not input_match:
                observation = "Lỗi: Cần xuất đúng định dạng gồm 'Action:' và 'Action Input:'."
            else:
                action_name = action_match.group(1).strip()
                raw_input = input_match.group(1).strip()
                raw_input = re.sub(r"^```json\s*", "", raw_input).strip("` ")
                
                try:
                    action_kwargs = json.loads(raw_input)
                    logger.log_event(f"Iteration_{i}", "Action", f"Gọi {action_name}")
                    print(f"Action Trích Xuất: {action_name} | Input: {action_kwargs}")
                    
                    if action_name in self.tools_map:
                        tool_func = self.tools_map[action_name]
                        output_path = tool_func(**action_kwargs) 
                        observation = f"Thành công. Kết quả file lưu tại: {output_path}"
                    else:
                        observation = f"Lỗi: Tool '{action_name}' không tồn tại."
                except Exception as e:
                    observation = f"Lỗi thực thi JSON/Tool: {e}"
            
            print(f"Observation từ Hệ Thống: {observation}")
            conversation_history += f"{response_text}\nObservation: {observation}\n"
            
        return "Agent đạt số bước giới hạn tối đa."
