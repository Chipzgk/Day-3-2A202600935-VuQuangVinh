import json
import os
from datetime import datetime

class AgentLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.log_dir, f"trace_{session_time}.jsonl")

    def log_event(self, step: str, event_type: str, content: str, metadata: dict = None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "event_type": event_type,
            "content": content,
        }
        if metadata:
            log_entry["metadata"] = metadata
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        print(f"[{event_type.upper()}] {content}")

logger = AgentLogger()
