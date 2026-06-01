import os
import time
import requests
from typing import Dict, Any, Optional, Generator
from src.core.llm_provider import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()
        if not self.api_key:
            raise ValueError("Thiếu GEMINI_API_KEY trong biến môi trường!")
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        url_headers = {"Content-Type": "application/json"}
        
        full_prompt = f"System Context & Instruction:\n{system_prompt}\n\nUser Request:\n{prompt}" if system_prompt else prompt
        payload = {"contents": [{"parts": [{"text": full_prompt}]}]}

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=url_headers, json=payload, timeout=10)
                
                if response.status_code == 200:
                    res_json = response.json()
                    content = res_json["candidates"][0]["content"]["parts"][0]["text"]
                    usage_meta = res_json.get("usageMetadata", {})
                    
                    return {
                        "content": content,
                        "usage": {
                            "prompt_tokens": usage_meta.get("promptTokenCount", 0),
                            "completion_tokens": usage_meta.get("candidatesTokenCount", 0),
                            "total_tokens": usage_meta.get("totalTokenCount", 0)
                        },
                        "latency_ms": int((time.time() - start_time) * 1000),
                        "provider": f"google_native ({self.model_name})"
                    }
                
                # TỐI ƯU: Rút ngắn thời gian ngủ để giảm tổng Latency hệ thống
                elif response.status_code in [429, 503]:
                    wait_time = 2 * (attempt + 1)
                    print(f"⚠️ [API] Server bận ({response.status_code}). Đang xả tải nhanh trong {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Lỗi HTTP {response.status_code}: {response.text}")
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(1)
                
        raise Exception(f"Không thể kết nối Live tới {self.model_name} sau {max_retries} lần thử.")

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        res = self.generate(prompt, system_prompt)
        yield res["content"]
