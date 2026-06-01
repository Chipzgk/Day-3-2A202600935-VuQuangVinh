import os
from typing import Optional
from src.core.llm_provider import LLMProvider
from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider

def create_provider_from_env() -> LLMProvider:
    """
    Creates and returns an instance of LLMProvider based on environment variables.
    Supported providers: openai, google/gemini, local.
    """
    provider = os.getenv("DEFAULT_PROVIDER", "openai").lower()
    
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            raise ValueError(
                "OPENAI_API_KEY is not set or has the placeholder value in the .env file. "
                "Please add a valid OpenAI API key to run with the 'openai' provider."
            )
        default_model = os.getenv("DEFAULT_MODEL", "gpt-4o")
        model_name = os.getenv("OPENAI_MODEL")
        if not model_name:
            if default_model and "gpt" in default_model.lower():
                model_name = default_model
            else:
                model_name = "gpt-4o"
        return OpenAIProvider(model_name=model_name, api_key=api_key)
        
    elif provider in ("google", "gemini"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError(
                "GEMINI_API_KEY is not set or has the placeholder value in the .env file. "
                "Please add a valid Gemini API key to run with the 'google/gemini' provider."
            )
        default_model = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")
        model_name = os.getenv("GEMINI_MODEL")
        if not model_name:
            if default_model and "gemini" in default_model.lower():
                model_name = default_model
            else:
                model_name = "gemini-2.5-flash"
        return GeminiProvider(model_name=model_name, api_key=api_key)
        
    elif provider == "local":
        try:
            from src.core.local_provider import LocalProvider
        except ImportError:
            raise ImportError(
                "The 'llama-cpp-python' library is required to run a local model but is not installed. "
                "Please run `pip install llama-cpp-python` to use the 'local' provider."
            )
            
        model_path = os.getenv("LOCAL_MODEL_PATH")
        if not model_path:
            raise ValueError("LOCAL_MODEL_PATH is not set in the .env file.")
        
        # Resolve path relative to project root if it is a relative path
        if not os.path.isabs(model_path):
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            abs_model_path = os.path.join(project_root, model_path)
        else:
            abs_model_path = model_path
            
        if not os.path.exists(abs_model_path):
            raise FileNotFoundError(
                f"Local model GGUF file not found at: {abs_model_path}\n"
                f"Please download a GGUF model and update the LOCAL_MODEL_PATH in your .env file."
            )
        return LocalProvider(model_path=abs_model_path)
        
    else:
        raise ValueError(
            f"Unsupported provider: '{provider}'. "
            "Supported providers are: 'openai', 'google' (or 'gemini'), 'local'"
        )
