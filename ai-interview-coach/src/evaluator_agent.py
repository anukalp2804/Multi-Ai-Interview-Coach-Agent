# evaluator_agent.py
from llm_adapters import get_llm
import os
import json

class EvaluatorAgent:
    def __init__(self, llm_adapter: str = None):
        adapter = llm_adapter or os.getenv("LLM_ADAPTER", "mock")
        self.llm = get_llm(adapter)

    def evaluate(self, question: dict, user_answer: str) -> dict:
        qtext = question.get("q", "")
        correct = question.get("answer", "")

        prompt = f"""
You are an interview evaluator. Compare the USER ANSWER with the CORRECT ANSWER.

RULES FOR SCORING:
- If user answer is unrelated → score = 0
- If partially correct → score = 1–3
- If missing important points → score = 4–6
- If mostly correct with minor mistakes → score = 7–9
- If fully correct and complete → score = 10

Return ONLY JSON:
{{
  "score": <0-10>,
  "feedback": "<analysis>",
  "suggestions": ["<tip1>", "<tip2>"]
}}

QUESTION: {qtext}
CORRECT ANSWER: {correct}
USER ANSWER: {user_answer}
"""

        result = self.llm.evaluate(qtext, user_answer, correct)

        score = int(result.get("score", 0))
        score = max(0, min(score, 10))  # clamp to 0–10 safely

        return {
            "score": score,
            "feedback": result.get("feedback", "No feedback."),
            "suggestions": result.get("suggestions", [])
        }
