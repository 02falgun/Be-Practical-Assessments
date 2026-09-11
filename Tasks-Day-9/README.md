# 🤖 Day 9: Gemini AI Engineering & Executive Resume Bullet Optimizer

Welcome to **Day 9: Gemini AI Engineering Portfolio Lab**. This directory contains the production-grade implementation of **"The Executive Resume Bullet & Impact Optimizer"** powered by the official Google GenAI SDK (`google-genai`).

---

## 📁 Directory Structure

```
chat-bot-test-Day-9/
├── .env                  # Secure environment file containing GEMINI_API_KEY (git-ignored)
├── .gitignore            # Git exclusion rules preventing credential leaks
├── requirements.txt      # Python dependencies
├── app.py                # Standalone, production-ready Python script
├── chat_bot_day_9.ipynb  # Interactive Jupyter / Google Colab Notebook
└── README.md             # Project documentation and usage guide
```

---

## 🚀 Key Modules & Concepts

### 1. Zero-Hardcoding Security (`.env` & `.gitignore`)
- API keys are never hardcoded. Loaded via `python-dotenv` or Google Colab Secrets (`userdata.get('GEMINI_API_KEY')`).
- `.gitignore` guarantees that `.env` is never committed to GitHub.

### 2. Pre-Flight Token & Cost Estimation
- Uses `client.models.count_tokens` prior to generation calls to accurately budget input token consumption and predict execution costs.

### 3. Production Resilience (Exponential Backoff with Jitter)
- Handles `APIError` (HTTP 429 rate limits, HTTP 500/503 transient errors, and timeouts).
- Formula: $\text{delay} = (\text{base\_delay} \times 2^{\text{attempt}}) + \text{random\_jitter}$ to avoid the Thundering Herd issue.

### 4. Statelessness & 3-Turn Contextual Memory
- Explicitly maintains the conversation history list of `{"role": "user" | "model", "parts": [...]}` turns to enable multi-turn dialogue and pronoun resolution.

### 5. Student Lab: Executive Resume Bullet Optimizer (Tasks 1–3)
- **Task 1: Pydantic Schema**: Defines strict types for:
  - `original_bullet`: Raw input text
  - `xyz_formatted_bullet`: Google XYZ formula ("Accomplished [X], as measured by [Y], by doing [Z]")
  - `impact_metric`: Quantifiable metric KPI
  - `action_verb`: Strong opening action verb
  - `seniority_score`: Integer rating (1–10)
  - `critique`: 1-sentence analytical critique
- **Task 2: Application Engine (`ResumeOptimizerEngine`)**:
  - `GenerateContentConfig` with `temperature=0.1`, `response_mime_type="application/json"`, and `response_schema=ResumeBulletOptimization`.
  - Structured output parsing with `model_validate_json()`.
  - Multi-turn revision history via `request_revision()`.
  - Robust retry wrapper via `execute_with_exponential_backoff()`.
- **Task 3: Test Real-World Cases**:
  - Tested on weak bullets (e.g. database tuning, React login, sales management).
  - Multi-turn interactive revision demonstration (refining to Principal Architect and Fortune 50 C-suite levels).

---

## 💻 How to Run

### Option A: Run Standalone Python Script
```bash
# 1. Navigate to the directory
cd "chat-bot-test-Day-9"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python app.py
```

### Option B: Run via Jupyter Notebook / Google Colab
1. Open `chat_bot_day_9.ipynb` in VS Code, JupyterLab, or upload to Google Colab.
2. Run all cells sequentially from top to bottom.
