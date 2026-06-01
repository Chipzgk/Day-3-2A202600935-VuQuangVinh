import os
from abc import ABC, abstractmethod
from openai import OpenAI

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Thiếu OPENAI_API_KEY trong biến môi trường!")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo" 

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2 
        )
        return response.choices[0].message.content

def get_llm_provider() -> LLMProvider:
    return OpenAIProvider()
