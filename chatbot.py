import os
import sys
import time
import argparse
from dotenv import load_dotenv

# Ensure the root of the project is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.provider_factory import create_provider_from_env
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

# Define the baseline demo prompts
DEMO_PROMPTS = [
    "Compose a lonely ballad idea in C major at 70 BPM.",
    "Create an energetic EDM drop concept at 128 BPM.",
    "Design a lo-fi chill-out beat for studying.",
    "Suggest a complex jazz chord progression with a mysterious mood.",
    "Create a cinematic epic soundtrack idea for a battle scene."
]

SYSTEM_PROMPT = (
    "You are an AI Music Composition Assistant. You help users design and conceptualize digital music.\n"
    "Because you are a text-only chatbot baseline, you must respond using only text-based suggestions "
    "(such as song concepts, chord progressions, melodies described in words, BPM, instrumentation, "
    "or arrangement plans).\n"
    "You must NOT attempt to use external tools, generate audio, render MIDI, or analyze actual sound. "
    "If requested to perform these operations, politely state that you are a text-only baseline chatbot "
    "and cannot execute actions or observe their outputs directly."
)

def print_banner():
    banner = """
======================================================================
    [MUSIC]  WELCOME TO THE AI MUSIC COMPOSITION ASSISTANT (BASELINE)
======================================================================
[INFO] Text-Only Baseline Chatbot Mode Active.
[INFO] No external tools, MIDI rendering, or audio processing available.
======================================================================
"""
    try:
        print(banner)
    except UnicodeEncodeError:
        # Fallback if there are any other unicode characters in terminal stream
        print(banner.encode('ascii', errors='replace').decode('ascii'))

def query_llm(provider, prompt: str) -> bool:
    """
    Sends a query to the LLM provider, logs performance metrics and events, and displays the response.
    Returns True if successful, False otherwise.
    """
    print(f"\nPrompt: \"{prompt}\"")
    print(f"Connecting to provider: {provider.__class__.__name__} ({provider.model_name})...")
    
    logger.log_event("CHATBOT_PROMPT", {"prompt": prompt})
    
    try:
        start_time = time.time()
        # Non-streaming response to capture exact token usage and latency
        response = provider.generate(prompt, system_prompt=SYSTEM_PROMPT)
        latency_ms = response.get("latency_ms", int((time.time() - start_time) * 1000))
        
        content = response.get("content", "")
        usage = response.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        provider_name = response.get("provider", "unknown")
        
        # Track metric using PerformanceTracker
        tracker.track_request(
            provider=provider_name,
            model=provider.model_name,
            usage=usage,
            latency_ms=latency_ms
        )
        
        # Log chatbot response event
        logger.log_event("CHATBOT_RESPONSE", {
            "prompt": prompt,
            "response": content,
            "latency_ms": latency_ms,
            "usage": usage,
            "provider": provider_name,
            "model": provider.model_name
        })
        
        print("\nResponse:")
        print("-" * 60)
        try:
            print(content)
        except UnicodeEncodeError:
            encoding = sys.stdout.encoding or 'ascii'
            print(content.encode(encoding, errors='replace').decode(encoding))
        print("-" * 60)
        print(f"Latency: {latency_ms} ms | Tokens: Prompt={usage.get('prompt_tokens')}, "
              f"Completion={usage.get('completion_tokens')}, Total={usage.get('total_tokens')}")
        print("=" * 60)
        return True
        
    except Exception as e:
        error_msg = f"Failed to generate response: {str(e)}"
        print(f"\n[ERROR] {error_msg}", file=sys.stderr)
        logger.log_event("CHATBOT_ERROR", {
            "prompt": prompt,
            "error": str(e)
        })
        return False

def run_demo(provider):
    print("\n--- Running Predefined Demo Prompts ---")
    for i, prompt in enumerate(DEMO_PROMPTS, 1):
        print(f"\nDemo Prompt {i}/{len(DEMO_PROMPTS)}")
        query_llm(provider, prompt)
        time.sleep(1) # Small pause between prompts

def run_interactive(provider):
    print("\n--- Starting Interactive Chat Mode ---")
    print("Type your music composition prompt below. Type 'exit', 'quit', or 'q' to end the session.")
    while True:
        try:
            prompt = input("\nYou > ").strip()
            if not prompt:
                continue
            if prompt.lower() in ("exit", "quit", "q"):
                print("Ending session. Goodbye!")
                break
            query_llm(provider, prompt)
        except (KeyboardInterrupt, EOFError):
            print("\nSession interrupted. Goodbye!")
            break

def main():
    parser = argparse.ArgumentParser(description="AI Music Composition Assistant - Baseline Chatbot CLI")
    parser.add_argument("--demo", action="store_true", help="Run the predefined music composition demo prompts.")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive CLI mode.")
    args = parser.parse_args()
    
    # Load .env file
    load_dotenv()
    
    session_start_time = time.time()
    
    # Initialize provider
    try:
        provider = create_provider_from_env()
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Failed to initialize provider from environment configurations.", file=sys.stderr)
        print(f"Error details: {e}", file=sys.stderr)
        print("Please check your .env file and ensure that the requested DEFAULT_PROVIDER and its API key are correct.", file=sys.stderr)
        sys.exit(1)
        
    print_banner()
    
    logger.log_event("CHATBOT_START", {
        "provider": provider.__class__.__name__,
        "model": provider.model_name
    })
    
    if args.demo:
        run_demo(provider)
    elif args.interactive:
        run_interactive(provider)
    else:
        # Default behavior: Ask user which mode to run if not specified
        print("Please choose a mode:")
        print("1. Run baseline demo prompts")
        print("2. Enter interactive chat mode")
        choice = input("Enter choice (1 or 2): ").strip()
        if choice == "1":
            run_demo(provider)
        elif choice == "2":
            run_interactive(choice_provider)
        else:
            print("Invalid selection. Defaulting to interactive mode.")
            run_interactive(provider)
            
    session_duration = int(time.time() - session_start_time)
    logger.log_event("CHATBOT_END", {
        "session_duration_sec": session_duration
    })

if __name__ == "__main__":
    main()
