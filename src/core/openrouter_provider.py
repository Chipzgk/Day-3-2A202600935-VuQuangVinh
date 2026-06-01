import os
import time
from openai import OpenAI
from typing import Dict, Any, Optional, Generator
from src.core.llm_provider import LLMProvider

class OpenRouterLiveProvider(LLMProvider):
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        # CHIẾN LƯỢC CHỐNG LỖI 404: Tạo bể chứa các model Free ổn định cao để tự động xoay tua live
        self.models_pool = [
            "google/gemini-2.5-flash:free",
            "qwen/qwen-2.5-7b-instruct:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemini-flash-1.5-8b:free"
        ]
        
        # Nếu có model chỉ định từ ngoài, ưu tiên đưa lên đầu hàng đợi
        if model_name:
            self.models_pool.insert(0, model_name)
            
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        last_exception = None
        
        # Duyệt qua từng phương án model cho đến khi kết nối thành công endpoint live
        for model in self.models_pool:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.2
                )
                
                end_time = time.time()
                content = response.choices[0].message.content
                
                # Trích xuất dữ liệu token thực tế từ API truyền về telemetry log
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }

                return {
                    "content": content,
                    "usage": usage,
                    "latency_ms": int((end_time - start_time) * 1000),
                    "provider": f"openrouter ({model})"
                }
            except Exception as e:
                last_exception = e
                # In cảnh báo lỗi endpoint để làm tư liệu đưa vào trace.md
                print(f"⚠️ [Endpoint Warning] Dòng model '{model}' báo lỗi hoặc đổi ID. Đang tự động luân chuyển sang dòng dự phòng...")
                continue
                
        raise Exception(f"Toàn bộ các endpoint trong bể chứa OpenRouter đều thất bại. Chi tiết lỗi cuối: {last_exception}")

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        res = self.generate(prompt, system_prompt)
        yield res["content"]
