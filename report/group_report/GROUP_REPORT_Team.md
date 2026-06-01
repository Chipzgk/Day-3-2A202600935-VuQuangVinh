# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: Kẻ lót đường
- **Team Members**: Vũ Quang Vinh, Hoàng Đức Dũng, Đinh Văn Anh Khôi, Đoàn Công Phú
- **Deployment Date**: 2026-06-01

---

## 1. Executive Summary

*Brief overview of the agent's goal and success rate compared to the baseline chatbot.*

- **Success Rate**: 29.4% aggregate reliability on 17 test cases (Baseline v1) -> 100% stable runtime after v2 Guardrails implementation.
- **Key Outcome**: The baseline agent successfully proved that an LLM can orchestrate local Python tools to synthesize physical `.wav` files. However, the system required strict pacing (throttling) and prompt constraints to survive Google API rate limits and prevent infinite loops.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation
The system utilizes a 5-step ReAct architecture (`max_iterations=5`). The LLM reads the user intent (`Thought`), formulates a JSON payload to call a tool (`Action`), the Python backend executes the tool and returns the file path (`Observation`), and the LLM closes the loop (`Final Answer`).

### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `create_midi` | `json` | Generates a structural `.mid` notation file based on tempo, key, and bars. |
| `midi_to_wav` | `json` | Synthesizer that reads `.mid` and applies a waveform to output audio. |
| `create_music_wav` | `json` | **(Active Tool)** All-in-one wrapper that combines MIDI generation and WAV rendering to reduce LLM reasoning steps. |

### 2.3 LLM Providers Used
- **Primary**: `gemini-2.5-flash` (via Google AI Studio `v1beta` endpoint).
- **Secondary (Backup)**: Direct Python Backend Execution (Disaster Recovery bypass when API is down).

---

## 3. Telemetry & Performance Dashboard

*Analyze the industry metrics collected during the final test run.*

- **Average Latency (P50)**: 2,939.3 ms per reasoning loop.
- **Max Latency (P99)**: > 23,000 ms (when HTTP 429 Exponential Backoff is triggered).
- **Average Tokens per Task**: ~235 Prompt Tokens / ~85 Completion Tokens (Total: 3,998 Prompt / 1,451 Completion over 17 runs).
- **Total Cost of Test Suite**: $0.00 (Utilized Google Free Tier).

---

## 4. Root Cause Analysis (RCA) - Failure Traces

*Deep dive into why the agent failed.*

### Case Study: Infinite Loop (Timeout / Max Steps Exceeded)
- **Input**: "Hãy làm cho tôi một đoạn nhạc lofi dài 8 bars, nhịp điệu chậm rãi 80 BPM, tone C."
- **Observation**: Agent successfully called `create_music_wav` and system returned `Thành công. Kết quả file lưu tại: outputs/lofi_chill.wav`.
- **Root Cause**: The agent failed to output `Final Answer`. Due to Context Drift in longer token windows, the LLM forgot to terminate the loop and hallucinated new tasks, hitting the iteration cap.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs Prompt v2 (Strict Constraints)
- **Diff**: Added rule: "Nếu Observation có chữ 'Thành công...', BẮT BUỘC KHÔNG gọi tool nữa và phải dùng Final Answer."
- **Result**: Reduced infinite loop `Timeout` errors by 100%, stabilizing the system to a Zero-Crash runtime.

### Experiment 2 (Bonus): Chatbot vs Agent
| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Simple Q (Music Theory) | Correct (Fast & Cheap) | Over-engineered (High Latency) | **Chatbot** |
| Multi-step (Generate Audio) | Hallucinated text only | Correct (Rendered .wav) | **Agent** |

---

## 6. Production Readiness Review

*Considerations for taking this system to a real-world environment.*

- **Security**: Implement JSON schema validation (e.g., Pydantic) to strictly sanitize the `Action Input` before passing it to the local `create_music_wav` tool.
- **Guardrails**: Limit `max_iterations=5` and insert a 2.5s `time.sleep()` between loops to prevent bursting the API rate limits.
- **Scaling**: Implement an intent-based `SmartRouter` at the API gateway to direct simple queries to the Chatbot and complex synthesis requests to the ReAct Agent, optimizing both cost and UX.
