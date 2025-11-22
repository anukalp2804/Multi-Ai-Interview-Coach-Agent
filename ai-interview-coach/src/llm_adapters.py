# llm_adapters.py
import os
import json
from typing import Dict, Any

# Mock evaluator (keeps previous behavior for offline mode)
from tools.scoring_utils import mock_evaluate_answer

# Try to import Google Generative AI (Gemini) SDK
try:
    import google.generativeai as genai
    GEMINI_SDK_AVAILABLE = True
except Exception:
    GEMINI_SDK_AVAILABLE = False

class MockLLM:
    def evaluate(self, question_text: str, user_answer: str, correct_answer: str) -> Dict[str, Any]:
        """
        Mock evaluate signature matches the real adapter.
        """
        # Use existing mock evaluator which expects (question, answer)
        # We'll provide user_answer for scoring.
        return mock_evaluate_answer(question_text, user_answer)

class GeminiAdapter:
    def __init__(self, model: str = "gemini-pro"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable not found.")
        if not GEMINI_SDK_AVAILABLE:
            raise RuntimeError("google.generativeai SDK is not installed in this environment.")
        genai.configure(api_key=api_key)
        self.model = model

    def _build_prompt(self, question_text: str, user_answer: str, correct_answer: str) -> str:
        """
        Build a prompt that instructs the model to return JSON only.
        """
        prompt = f"""
You are an experienced interview evaluator.

Compare the USER ANSWER with the CORRECT ANSWER (reference). Evaluate accuracy, completeness, and clarity.

Return ONLY valid JSON with the exact keys: score, feedback, suggestions.

JSON format:
{{
  "score": <integer 0-10>,
  "feedback": "<brief constructive feedback>",
  "suggestions": ["<suggestion1>", "<suggestion2>"]
}}

QUESTION:
{question_text}

REFERENCE (Correct) ANSWER:
{correct_answer}

USER ANSWER:
{user_answer}

Important: Output must be valid JSON and nothing else.
"""
        return prompt

    def evaluate(self, question_text: str, user_answer: str, correct_answer: str) -> Dict[str, Any]:
        prompt = self._build_prompt(question_text, user_answer, correct_answer)
        try:
            # Use genai.generate (SDK versions vary — this attempts a safe call)
            resp = genai.generate(model=self.model, prompt=prompt, max_output_tokens=512)
            # The response shape may differ between SDK versions. Try to extract text robustly.
            text = None
            # Newer SDK returns resp.result[0].content[0].text (or resp.output[0].content[0].text)
            if hasattr(resp, "result"):
                try:
                    text = resp.result[0].content[0].text
                except Exception:
                    text = str(resp)
            else:
                # Some versions return resp.text or str(resp)
                text = getattr(resp, "text", None) or str(resp)

            # Try to find JSON within the text (strip surrounding whitespace)
            text = text.strip()
            # If the model added backticks or code fences, try to clean them
            if text.startswith("```"):
                # remove code fences
                parts = text.split("```")
                # pick the longest chunk that looks like JSON
                text = max(parts, key=len).strip()

            # Parse JSON
            parsed = json.loads(text)
            # Ensure keys
            score = int(parsed.get("score", 0))
            feedback = parsed.get("feedback", "")
            suggestions = parsed.get("suggestions", []) or []
            # Normalize suggestions to list of strings
            suggestions = [str(s) for s in suggestions][:5]
            return {"score": score, "feedback": feedback, "suggestions": suggestions}
        except Exception as e:
            # On any failure, fall back to mock grader
            print("GeminiAdapter.evaluate fallback to mock due to:", e)
            return mock_evaluate_answer(question_text, user_answer)

def get_llm(adapter: str = None):
    """
    Factory to get an LLM adapter.
    adapter: "gemini" or "mock" (default picks env LLM_ADAPTER or 'mock')
    """
    adapter = (adapter or os.getenv("LLM_ADAPTER") or "mock").lower()
    if adapter == "gemini":
        try:
            return GeminiAdapter()
        except Exception as e:
            print("Failed to initialize GeminiAdapter:", e)
            print("Falling back to MockLLM.")
            return MockLLM()
    return MockLLM()
