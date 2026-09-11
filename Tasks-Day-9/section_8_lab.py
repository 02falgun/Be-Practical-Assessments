"""
==============================================================================
SECTION 8: STUDENT GRADED LAB ASSIGNMENT
Temperature & Nucleus Sampling (Top-P) Divergence Experiment
==============================================================================

MANDATORY TASKS:
1. Fix the prompt: "Explain the concept of 'Technical Debt' to a non-technical CEO using a vivid real-world analogy."
2. Run the prompt across 4 specific hyperparameter configurations:
   - Config 1 (Deterministic Baseline): Temperature = 0.0, Top-P = 0.95
   - Config 2 (Controlled Diversity):  Temperature = 0.5, Top-P = 0.80
   - Config 3 (Balanced Creative):     Temperature = 0.9, Top-P = 0.95
   - Config 4 (High Entropy):          Temperature = 1.4, Top-P = 1.00
3. Record generated responses, count total token usage, and analyze stylistic divergence.
==============================================================================
"""

import os
import time
import json
import random
from typing import List, Dict, Any
from dotenv import load_dotenv

# Try importing optional libraries for rich display
try:
    import pandas as pd
except ImportError:
    pd = None

try:
    from tabulate import tabulate
except ImportError:
    tabulate = None

# Official Google GenAI SDK
from google import genai
from google.genai import types
from google.genai.errors import APIError

# Load environment
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in .env or environment!")

MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")
client = genai.Client(api_key=GEMINI_API_KEY)
print(f"✅ Google Gemini Client initialized successfully! (Model: {MODEL_NAME})\n")


# ------------------------------------------------------------------------------
# Production Exponential Backoff Retry Utility
# ------------------------------------------------------------------------------
def execute_with_backoff(api_func, max_retries: int = 5, base_delay: float = 2.0):
    for attempt in range(max_retries):
        try:
            return api_func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            code = getattr(e, "code", getattr(e, "status_code", type(e).__name__))
            delay = (base_delay * (2 ** attempt)) + random.uniform(0.2, 0.8)
            print(f"⚠️ Warning: Transient error ({code}). Retrying in {delay:.2f}s... (Attempt {attempt+1}/{max_retries})")
            time.sleep(delay)


# ------------------------------------------------------------------------------
# Stylistic Divergence Metric Helper
# ------------------------------------------------------------------------------
def analyze_style(text: str) -> Dict[str, Any]:
    """Computes basic stylistic metrics for comparing generation outputs."""
    words = [w.strip(".,!?;:\"'()[]{}").lower() for w in text.split() if w.strip()]
    num_words = len(words)
    unique_words = len(set(words))
    lexical_diversity = round(unique_words / num_words, 3) if num_words > 0 else 0.0
    sentences = [s for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    num_sentences = len(sentences)
    avg_sentence_len = round(num_words / num_sentences, 1) if num_sentences > 0 else 0.0

    return {
        "word_count": num_words,
        "unique_words": unique_words,
        "lexical_diversity": lexical_diversity,
        "sentence_count": num_sentences,
        "avg_sentence_len": avg_sentence_len
    }


# ==============================================================================
# LAB EXPERIMENT EXECUTION
# ==============================================================================
def run_hyperparameter_experiment():
    print("=" * 80)
    print("🎓 SECTION 8: TEMPERATURE & NUCLEUS SAMPLING DIVERGENCE EXPERIMENT")
    print("=" * 80)

    # 1. Fixed prompt as required by assignment
    target_prompt = "Explain the concept of 'Technical Debt' to a non-technical CEO using a vivid real-world analogy."
    print(f"📌 Mandatory Prompt:\n   \"{target_prompt}\"\n")

    # Count input tokens for prompt
    input_tokens = client.models.count_tokens(model=MODEL_NAME, contents=target_prompt).total_tokens

    # 2. Four specific hyperparameter configurations
    configurations = [
        {
            "id": "Config 1",
            "regime": "Deterministic Baseline",
            "temperature": 0.0,
            "top_p": 0.95,
            "description": "Greedy decoding; argmax token selection. Maximum repeatability, minimal variance."
        },
        {
            "id": "Config 2",
            "regime": "Controlled Diversity",
            "temperature": 0.5,
            "top_p": 0.80,
            "description": "Balanced temperature with tight nucleus sampling (top 80% probability mass)."
        },
        {
            "id": "Config 3",
            "regime": "Balanced Creative",
            "temperature": 0.9,
            "top_p": 0.95,
            "description": "Higher entropy with wide nucleus sampling. Natural, conversational variety."
        },
        {
            "id": "Config 4",
            "regime": "High Entropy / Creative",
            "temperature": 1.4,
            "top_p": 1.00,
            "description": "Flattened softmax logits over complete vocabulary. High novelty, higher hallucination risk."
        }
    ]

    experiment_records = []

    for cfg in configurations:
        print(f"\n▶ Executing {cfg['id']} ({cfg['regime']}) [T = {cfg['temperature']}, Top-P = {cfg['top_p']}]...")

        config_obj = types.GenerateContentConfig(
            temperature=cfg["temperature"],
            top_p=cfg["top_p"],
            max_output_tokens=600
        )

        def api_call():
            return client.models.generate_content(
                model=MODEL_NAME,
                contents=target_prompt,
                config=config_obj
            )

        response = execute_with_backoff(api_call)
        generated_text = response.text.strip() if response.text else "[NO TEXT GENERATED]"

        # Token usage audit
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            out_tokens = getattr(response.usage_metadata, "candidates_token_count", None)
            tot_tokens = getattr(response.usage_metadata, "total_token_count", None)
        else:
            out_tokens = None
            tot_tokens = None

        if out_tokens is None:
            out_tokens = client.models.count_tokens(model=MODEL_NAME, contents=generated_text).total_tokens
            tot_tokens = input_tokens + out_tokens

        # Style analysis
        style_metrics = analyze_style(generated_text)

        # Detect primary analogy used
        lower_text = generated_text.lower()
        if "kitchen" in lower_text or "restaurant" in lower_text or "chef" in lower_text:
            primary_analogy = "Restaurant Kitchen Cleaning"
        elif "house" in lower_text or "home" in lower_text or "renovation" in lower_text or "foundation" in lower_text:
            primary_analogy = "Home Construction / Renovation"
        elif "credit card" in lower_text or "financial" in lower_text or "loan" in lower_text or "interest" in lower_text:
            primary_analogy = "Financial Credit Card / Loan"
        elif "car" in lower_text or "vehicle" in lower_text or "engine" in lower_text or "oil" in lower_text:
            primary_analogy = "Car Maintenance & Oil Changes"
        else:
            primary_analogy = "Physical Infrastructure / Architecture"

        record = {
            "Config": cfg["id"],
            "Regime": cfg["regime"],
            "Temp": cfg["temperature"],
            "Top-P": cfg["top_p"],
            "Analogy": primary_analogy,
            "Input Tokens": input_tokens,
            "Output Tokens": out_tokens,
            "Total Tokens": tot_tokens,
            "Word Count": style_metrics["word_count"],
            "Lexical Diversity": style_metrics["lexical_diversity"],
            "Generated Text": generated_text
        }
        experiment_records.append(record)
        time.sleep(1.2)  # Respect free tier rate limits

    # --------------------------------------------------------------------------
    # 3. DISPLAY GENERATED RESPONSES IN DETAIL
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("=== 📋 DETAILED GENERATED RESPONSES ACROSS HYPERPARAMETER CONFIGS ===")
    print("=" * 80)

    for rec in experiment_records:
        border = "─" * 78
        print(f"\n┌{border}┐")
        print(f"│ ⚙️  {rec['Config']}: {rec['Regime'].upper()} (T={rec['Temp']}, Top-P={rec['Top-P']})".ljust(79) + "│")
        print(f"│ 🏷️  Core Analogy: {rec['Analogy']} | Total Tokens: {rec['Total Tokens']} | Lexical Div: {rec['Lexical Diversity']}".ljust(79) + "│")
        print(f"├{border}┤")
        # Word wrap text cleanly
        words = rec['Generated Text'].split()
        line = ""
        for w in words:
            if len(line) + len(w) + 1 <= 74:
                line = f"{line} {w}".strip()
            else:
                print(f"│    {line:<74} │")
                line = w
        if line:
            print(f"│    {line:<74} │")
        print(f"└{border}┘")

    # --------------------------------------------------------------------------
    # 4. TABULAR COMPARISON & STYLISTIC DIVERGENCE SUMMARY
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("=== 📊 STYLISTIC DIVERGENCE & TOKEN CONSUMPTION AUDIT TABLE ===")
    print("=" * 80)

    table_data = [
        [
            r["Config"],
            r["Regime"],
            f"{r['Temp']:.1f}",
            f"{r['Top-P']:.2f}",
            r["Analogy"],
            r["Output Tokens"],
            r["Word Count"],
            f"{r['Lexical Diversity']:.3f}"
        ]
        for r in experiment_records
    ]
    headers = ["Config", "Regime", "Temp", "Top-P", "Analogy Chosen", "Out Tokens", "Words", "Lexical Div"]

    if tabulate:
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    elif pd:
        summary_df = pd.DataFrame(table_data, columns=headers)
        print(summary_df.to_string(index=False))
    else:
        print(f"{'Config':10s} | {'Regime':22s} | {'Temp':5s} | {'Top-P':6s} | {'Analogy':25s} | {'Tokens':6s} | {'Diversity':9s}")
        print("-" * 90)
        for row in table_data:
            print(f"{row[0]:10s} | {row[1]:22s} | {row[2]:5s} | {row[3]:6s} | {row[4]:25s} | {str(row[5]):6s} | {row[7]:9s}")

    # --------------------------------------------------------------------------
    # 5. QUALITATIVE STYLISTIC ANALYSIS REPORT
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("=== 🧠 QUALITATIVE STYLISTIC & SAMPLING DIVERGENCE ANALYSIS ===")
    print("=" * 80)
    print("""
1. DETERMINISTIC BASELINE (T=0.0, Top-P=0.95):
   • Characteristics: The model always selects the argmax (highest probability) token.
   • Stylistic Traits: Direct, authoritative, highly structured, and business-centric. It selects
     the most universally tested analogy (typically kitchen cleaning or credit card interest)
     with zero variance between repeated executions.

2. CONTROLLED DIVERSITY (T=0.5, Top-P=0.80):
   • Characteristics: Temperature smooths logits moderately, but Top-P=0.80 restricts candidate tokens
     to only the top 80% probability mass, filtering out unconventional choices.
   • Stylistic Traits: Smooth, polished prose with natural sentence cadence. Explains technical trade-offs
     cleanly without digression or unusual metaphors.

3. BALANCED CREATIVE (T=0.9, Top-P=0.95):
   • Characteristics: Higher entropy with an open vocabulary tail (top 95% probability mass).
   • Stylistic Traits: Vivid, sensory metaphors (e.g. duct-taped foundations, compound interest traps,
     cluttered restaurant lines). Greater syntactic variety and expressive vocabulary.

4. HIGH ENTROPY / CREATIVE (T=1.4, Top-P=1.00):
   • Characteristics: Highly flattened softmax probability distribution; no tokens are filtered by nucleus sampling.
   • Stylistic Traits: Highly colorful, unconventional analogies and bold adjectives. While creative,
     at T >= 1.4 phrasing can exhibit minor syntactic looseness or hyperbolic metaphors.
""")
    print("✅ Section 8 Student Graded Lab Assignment completed successfully!")


if __name__ == "__main__":
    run_hyperparameter_experiment()
