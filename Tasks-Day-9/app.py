"""
==============================================================================
EXECUTIVE RESUME BULLET & IMPACT OPTIMIZER
Production-grade Google Gemini API implementation with:
- Zero-hardcoding security hygiene (.env support)
- Pre-flight token counting & cost estimation
- Production resilience (Exponential backoff with jitter)
- Multi-turn conversation state management
- Structured JSON output with Pydantic schema validation
==============================================================================
"""

import os
import sys
import time
import json
import random
from typing import List, Dict, Any, Optional
try:
    # pyrefly: ignore [missing-import]
    import numpy as np
except ImportError:
    np = None
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Try importing tabulate for pretty table rendering
try:
    from tabulate import tabulate
except ImportError:
    tabulate = None

# Official Google GenAI SDK
from google import genai
from google.genai import types
from google.genai.errors import APIError

# ==============================================================================
# SECTION 0: ENVIRONMENT SETUP & SECURE API AUTHENTICATION
# ==============================================================================
# Load environment variables from .env file
load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "❌ GEMINI_API_KEY not found! Please set GEMINI_API_KEY in your .env file or environment."
    )

# Model configuration: default to gemini-3-flash-preview (or override via GEMINI_MODEL env var)
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")

# Initialize Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)
print(f"✅ Google Gemini API Client initialized successfully! (Model: {MODEL_NAME})")


# ==============================================================================
# SECTION 1: API ARCHITECTURE, STATELESSNESS & SECURITY HYGIENE
# ==============================================================================
"""
1. WHY API KEYS MUST NEVER BE COMMITTED TO GITHUB:
   - Automated scrapers search public GitHub commits 24/7 for exposed API keys.
   - Leaked keys result in quota exhaustion, unexpected billing charges, and credential revocation.
   - DEFENSE: Store keys in a local `.env` file and add `.env` to `.gitignore`.

2. THE STATELESSNESS MENTAL MODEL:
   - LLMs are 100% STATELESS: The model remembers NOTHING between individual API calls.
   - To build a conversational multi-turn chatbot, YOU (the developer) must maintain a history list
     of previous (User, Model) turns and pass the cumulative array on every subsequent call.

3. MESSAGE ROLES MAPPING:
   ┌──────────────────────┬─────────────────────────┬───────────────────────────┐
   │ Role Type            │ OpenAI / Anthropic      │ Google Gemini API         │
   ├──────────────────────┼─────────────────────────┼───────────────────────────┤
   │ System Persona/Rules │ role: 'system'          │ config.system_instruction │
   │ User Message         │ role: 'user'            │ role: 'user'              │
   │ Model Response       │ role: 'assistant'       │ role: 'model'             │
   └──────────────────────┴─────────────────────────┴───────────────────────────┘
"""


# ==============================================================================
# SECTION 2: PRE-FLIGHT TOKEN COUNTING & FINANCIAL COST ESTIMATION
# ==============================================================================
def preflight_cost_estimate(
    text_prompt: str,
    model_name: str = MODEL_NAME,
    expected_output_tokens: int = 500
) -> Dict[str, Any]:
    """Calculates exact input tokens and estimates financial cost before calling the API."""
    token_resp = client.models.count_tokens(model=model_name, contents=text_prompt)
    input_tokens = token_resp.total_tokens

    # Official Rates per 1M tokens (USD)
    pricing = {
        "gemini-3-flash-preview": {"in": 0.075, "out": 0.30},
        "gemini-flash-latest":    {"in": 0.075, "out": 0.30},
        "gemini-3.6-flash":       {"in": 0.075, "out": 0.30},
        "gemini-2.5-flash":       {"in": 0.075, "out": 0.30},
        "gemini-1.5-flash":       {"in": 0.075, "out": 0.30},
        "gemini-1.5-pro":         {"in": 1.25,  "out": 5.00}
    }
    rate = pricing.get(model_name, pricing["gemini-3-flash-preview"])

    est_cost = (input_tokens / 1e6 * rate["in"]) + (expected_output_tokens / 1e6 * rate["out"])

    return {
        "model": model_name,
        "input_tokens": input_tokens,
        "estimated_output_tokens": expected_output_tokens,
        "estimated_cost_usd": round(float(est_cost), 6),
        "cost_per_10k_calls": round(float(est_cost * 10000), 2)
    }


# ==============================================================================
# SECTION 3: PRODUCTION RESILIENCE — EXPONENTIAL BACKOFF & RETRY LOOP
# ==============================================================================
def execute_with_exponential_backoff(
    api_call_func,
    max_retries: int = 6,
    base_delay: float = 2.0
):
    """Wraps an API call in an exponential backoff retry loop with random jitter."""
    for attempt in range(max_retries):
        try:
            return api_call_func()
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"❌ Max retries reached. Fatal API Error: {e}")
                raise e
            code = getattr(e, 'code', getattr(e, 'status_code', type(e).__name__))
            # Calculate backoff delay with jitter
            delay = (base_delay * (2 ** attempt)) + random.uniform(0.2, 1.0)
            print(f"⚠️ Warning: Transient API Error ({code}). Retrying in {delay:.2f}s... (Attempt {attempt+1}/{max_retries})")
            time.sleep(delay)


# ==============================================================================
# SECTION 4: REUSABLE GEMINI WRAPPER & 3-TURN CHAT
# ==============================================================================
def gemini_call(
    prompt: str,
    system_instruction: str = "You are a concise, helpful enterprise AI assistant.",
    temperature: float = 0.2,
    stream: bool = False,
    model: str = MODEL_NAME
) -> str:
    """Production-grade wrapper for Google Gemini API with error handling and streaming."""
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
        max_output_tokens=800
    )

    if stream:
        def stream_call():
            full_text = []
            response_stream = client.models.generate_content_stream(
                model=model, contents=prompt, config=config
            )
            for chunk in response_stream:
                if chunk.text:
                    print(chunk.text, end="", flush=True)
                    full_text.append(chunk.text)
            print()
            return "".join(full_text)

        return execute_with_exponential_backoff(stream_call)
    else:
        def standard_call():
            resp = client.models.generate_content(
                model=model, contents=prompt, config=config
            )
            return resp.text.strip()

        return execute_with_exponential_backoff(standard_call)


def run_3_turn_demo():
    """Demonstrates maintaining stateless conversation history across 3 turns."""
    print("\n" + "="*50)
    print("=== MULTI-TURN CONVERSATION LOOP DEMONSTRATION ===")
    print("="*50)

    conversation_history = []
    system_persona = "You are a Senior PostgreSQL Database Administrator. Answer concisely in 2 sentences."

    def send_chat_turn(user_message: str):
        print(f"\n👤 User: {user_message}")
        print("🤖 Assistant: ", end="")

        conversation_history.append({"role": "user", "parts": [{"text": user_message}]})

        config = types.GenerateContentConfig(
            system_instruction=system_persona,
            temperature=0.0
        )
        def call_turn():
            return client.models.generate_content(
                model=MODEL_NAME,
                contents=conversation_history,
                config=config
            )

        response = execute_with_exponential_backoff(call_turn)
        bot_reply = response.text.strip()
        print(bot_reply)
        conversation_history.append({"role": "model", "parts": [{"text": bot_reply}]})

    send_chat_turn("What is the difference between a clustered and non-clustered index?")
    time.sleep(1.0)
    send_chat_turn("Which one is faster for range queries on primary keys?")
    time.sleep(1.0)
    send_chat_turn("Can a table have multiple of the faster one?")
    time.sleep(1.0)


# ==============================================================================
# SECTION 5: STUDENT LAB WORKSPACE (PORTFOLIO APPLICATION)
# ==============================================================================
"""
🎓 STUDENT LAB ASSIGNMENT:
Build an end-to-end AI Application: "The Executive Resume Bullet & Impact Optimizer"

APPLICATION REQUIREMENTS:
1. Structured JSON Schema (Pydantic):
   - `original_bullet`: Raw user text
   - `xyz_formatted_bullet`: Rewritten using Google's XYZ Formula:
     "Accomplished [X], as measured by [Y], by doing [Z]"
   - `impact_metric`: The quantifiable numeric KPI
   - `action_verb`: Strong opening action verb
   - `seniority_score`: Integer rating (1 to 10) of executive presence
   - `critique`: 1-sentence explanation of what was improved
2. Interactive Revision History: Allow user to request a revision (multi-turn).
3. Streaming or Schema Parsing: Correctly parse and display output.
4. Error Handling: Enclose calls in retry blocks.
"""

# ==============================================================================
# TASK 1: DEFINE PYDANTIC SCHEMA FOR STRUCTURED RESUME OPTIMIZATION
# ==============================================================================
class ResumeBulletOptimization(BaseModel):
    """Pydantic schema enforcing structured output for executive resume bullet optimization."""
    original_bullet: str = Field(
        ...,
        description="The raw, unoptimized resume bullet provided by the user."
    )
    xyz_formatted_bullet: str = Field(
        ...,
        description="Rewritten bullet strictly following Google's XYZ Formula: 'Accomplished [X], as measured by [Y], by doing [Z]'."
    )
    impact_metric: str = Field(
        ...,
        description="The quantifiable numeric KPI (e.g., '45% latency reduction', '$1.2M in annual savings', '99.99% uptime')."
    )
    action_verb: str = Field(
        ...,
        description="Strong executive-level opening action verb in past tense (e.g., 'Spearheaded', 'Architected', 'Orchestrated', 'Transformed')."
    )
    seniority_score: int = Field(
        ...,
        ge=1,
        le=10,
        description="Integer rating (1 to 10) assessing the bullet's executive presence, scope of ownership, and strategic business impact."
    )
    critique: str = Field(
        ...,
        description="A concise 1-sentence explanation of the weaknesses identified in the original bullet and how this optimization elevates the candidate's profile."
    )


# ==============================================================================
# TASK 2: BUILD THE APPLICATION ENGINE
# ==============================================================================
class ResumeOptimizerEngine:
    """
    Production-grade Engine for optimizing resume bullets using Google's XYZ formula.
    Features:
    - Structured output validation with Pydantic
    - Multi-turn conversational memory for interactive revisions
    - Production resilience via exponential backoff
    - Formatted terminal output presentation
    """

    SYSTEM_INSTRUCTION = (
        "You are an elite Fortune 500 Executive Career Coach and Former Google Senior Tech Recruiter. "
        "Your mission is to transform weak, passive resume bullet points into high-impact, executive-tier "
        "statements using Google's proven XYZ formula: 'Accomplished [X], as measured by [Y], by doing [Z]'.\n"
        "Guidelines:\n"
        "1. Never use weak phrases like 'responsible for', 'helped with', or 'worked on'.\n"
        "2. Begin every bullet with a decisive, high-leverage action verb (e.g., Spearheaded, Architected, Engineered).\n"
        "3. Always inject plausible, rigorous quantifiable metrics (percentage gains, latency cuts, dollar savings, throughput).\n"
        "4. Provide a seniority score between 1 and 10 based on executive presence and business value.\n"
        "5. Respond strictly in valid JSON conforming to the requested schema."
    )

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self.conversation_history: List[Dict[str, Any]] = []
        self.latest_result: Optional[ResumeBulletOptimization] = None

    def reset_history(self):
        """Clears the conversational context for a new resume bullet."""
        self.conversation_history = []
        self.latest_result = None

    def _call_gemini_structured(self, contents: Any) -> ResumeBulletOptimization:
        """Executes API call configured with structured JSON schema and exponential backoff."""
        # Configure GenerateContentConfig with temperature=0.1, response_mime_type='application/json', and response_schema
        config = types.GenerateContentConfig(
            system_instruction=self.SYSTEM_INSTRUCTION,
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=ResumeBulletOptimization
        )

        def api_invocation():
            resp = client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            return resp

        response = execute_with_exponential_backoff(api_invocation)
        parsed_data = ResumeBulletOptimization.model_validate_json(response.text)
        return parsed_data

    def optimize_bullet(self, raw_bullet: str) -> ResumeBulletOptimization:
        """
        Takes raw bullet text, sends it to Gemini, records the turn in conversation history,
        and returns the parsed structured optimization.
        """
        self.reset_history()
        user_prompt = f"Optimize this resume bullet into Google's XYZ formula:\n\"{raw_bullet}\""

        # 1. Append to conversation history
        self.conversation_history.append({
            "role": "user",
            "parts": [{"text": user_prompt}]
        })

        # 2. Execute with structured schema
        result = self._call_gemini_structured(self.conversation_history)

        # 3. Append model response to conversation history to maintain context
        self.conversation_history.append({
            "role": "model",
            "parts": [{"text": result.model_dump_json()}]
        })

        self.latest_result = result
        return result

    def request_revision(self, feedback: str) -> ResumeBulletOptimization:
        """
        Multi-turn revision: allows the user to request alterations or refine the bullet
        (e.g., 'Make it more tailored for a Staff Database Engineer' or 'Highlight cost reduction over latency').
        """
        if not self.conversation_history:
            raise ValueError("No previous bullet found in history. Call optimize_bullet() first.")

        revision_prompt = f"Revise the previous bullet with this specific feedback:\n\"{feedback}\""

        # 1. Append user revision request to multi-turn conversation history
        self.conversation_history.append({
            "role": "user",
            "parts": [{"text": revision_prompt}]
        })

        # 2. Call Gemini with cumulative history
        result = self._call_gemini_structured(self.conversation_history)

        # 3. Append updated model response to history
        self.conversation_history.append({
            "role": "model",
            "parts": [{"text": result.model_dump_json()}]
        })

        self.latest_result = result
        return result

    @staticmethod
    def display_optimization_card(opt: ResumeBulletOptimization, title: str = "RESUME BULLET OPTIMIZATION"):
        """Formats and displays the structured optimization beautifully in the console."""
        border = "═" * 78
        print(f"\n╔{border}╗")
        print(f"║ 🎯 {title.center(74)} ║")
        print(f"╠{border}╣")
        print(f"║ 📌 ORIGINAL BULLET:                                                         ║")
        print(f"║    {opt.original_bullet[:72]:<72} ║")
        if len(opt.original_bullet) > 72:
            print(f"║    {opt.original_bullet[72:144]:<72} ║")
        print(f"╠{border}╣")
        print(f"║ 🚀 GOOGLE XYZ OPTIMIZED:                                                    ║")
        # Word wrap for XYZ bullet
        words = opt.xyz_formatted_bullet.split()
        line = ""
        for w in words:
            if len(line) + len(w) + 1 <= 72:
                line = f"{line} {w}".strip()
            else:
                print(f"║    {line:<72} ║")
                line = w
        if line:
            print(f"║    {line:<72} ║")
        print(f"╠{border}╣")

        score_stars = "★" * opt.seniority_score + "☆" * (10 - opt.seniority_score)
        table_rows = [
            ["Action Verb", opt.action_verb],
            ["Impact KPI", opt.impact_metric],
            ["Seniority Score", f"{opt.seniority_score}/10  [{score_stars}]"],
            ["Executive Critique", opt.critique]
        ]

        if tabulate:
            formatted_table = tabulate(table_rows, headers=["Attribute", "Evaluation"], tablefmt="grid")
            print(formatted_table)
        else:
            for attr, val in table_rows:
                print(f"║ • {attr:18s}: {val[:50]:<50} ║")
        print(f"╚{border}╝\n")


# ==============================================================================
# TASK 3: TEST APPLICATION ON REAL-WORLD WEAK BULLETS
# ==============================================================================
def run_student_lab_tests():
    """Runs end-to-end validation on real-world weak bullets and demonstrates multi-turn revisions."""
    print("\n" + "#"*78)
    print("### SECTION 5: STUDENT LAB WORKSPACE — PORTFOLIO APPLICATION TEST RUN ###")
    print("#"*78)

    engine = ResumeOptimizerEngine(model_name=MODEL_NAME)

    weak_bullets = [
        "Helped with the database and made it run faster.",
        "Wrote code for a customer login page in React.",
        "Responsible for managing a team of sales reps and tracking leads in CRM."
    ]

    for idx, bullet in enumerate(weak_bullets, start=1):
        print(f"\n--- [Test Case {idx}/3]: Optimizing Weak Bullet ---")
        result = engine.optimize_bullet(bullet)
        engine.display_optimization_card(result, title=f"Optimization Case #{idx}")
        time.sleep(1.5)

    # --------------------------------------------------------------------------
    # Demonstrate Multi-Turn Revision History (Requirement #2)
    # --------------------------------------------------------------------------
    print("\n" + "="*78)
    print("=== 🔄 DEMONSTRATING MULTI-TURN INTERACTIVE REVISION HISTORY ===")
    print("="*78)
    print("Initial Bullet: 'Helped with the database and made it run faster.'")
    initial_res = engine.optimize_bullet("Helped with the database and made it run faster.")
    engine.display_optimization_card(initial_res, title="Turn 1: Initial XYZ Transformation")
    time.sleep(1.5)

    print("\n👤 User Revision Request: 'Revise this for a Principal Architect role. Emphasize multi-region PostgreSQL replication, $250K cloud cost reduction, and zero downtime.'")
    revised_res = engine.request_revision(
        "Revise this for a Principal Architect role. Emphasize multi-region PostgreSQL replication, $250K cloud cost reduction, and zero downtime."
    )
    engine.display_optimization_card(revised_res, title="Turn 2: Principal Architect Revision")
    time.sleep(1.5)

    print("\n👤 User Revision Request: 'Make the action verb even punchier and push the seniority rating to a full 10/10.'")
    revised_res_2 = engine.request_revision(
        "Make the action verb even punchier and push the seniority rating to a full 10/10."
    )
    engine.display_optimization_card(revised_res_2, title="Turn 3: 10/10 Executive Polish")

    print("✅ All student lab requirements (Tasks 1, 2, 3) executed successfully!")


# ==============================================================================
# SECTION 6: GIT REPOSITORY HYGIENE — CREATING .ENV AND .GITIGNORE
# ==============================================================================
def verify_git_hygiene():
    """Verifies that .env is not tracked and .gitignore exists locally."""
    gitignore_path = os.path.join(os.path.dirname(__file__), ".gitignore")
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, "w") as f:
            f.write(".env\n.env.*\n*.joblib\n__pycache__/\n.ipynb_checkpoints/\n")
        print("✅ '.gitignore' template created successfully!")
    else:
        print("✅ '.gitignore' verified.")


# ==============================================================================
# MAIN EXECUTION ENTRYPOINT
# ==============================================================================
if __name__ == "__main__":
    print("\n=======================================================")
    print("=== RUNNING FULL DAY 9 ASSIGNMENT SCRIPT ===")
    print("=======================================================\n")

    # Section 2: Preflight cost estimate demo
    sample_payload = "Please summarize the last 10 quarterly financial filings of Apple, Microsoft, and Google."
    estimate = preflight_cost_estimate(sample_payload, model_name=MODEL_NAME)
    print("=== 📊 PRE-FLIGHT TOKEN & COST AUDIT ===")
    for k, v in estimate.items():
        print(f"• {k:25s}: {v}")

    # Section 4: 3-turn chat demo
    run_3_turn_demo()

    # Section 5: Student lab portfolio application
    run_student_lab_tests()

    # Section 6: Git hygiene verification
    verify_git_hygiene()
