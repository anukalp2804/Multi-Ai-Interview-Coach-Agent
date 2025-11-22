# interviewer_agent.py
import json
import random
from pathlib import Path
from typing import Dict, Any

class InterviewerAgent:
    def __init__(self, question_bank_path: Path):
        with open(question_bank_path, "r", encoding="utf-8") as f:
            self.bank = json.load(f)
        # track per-session pointers externally (or orchestrator will manage)

    def pick_question(self, domain: str, difficulty: str, exclude_ids=None) -> Dict[str,Any]:
        exclude_ids = exclude_ids or []
        candidates = self.bank.get(domain, {}).get(difficulty, [])
        candidates = [c for c in candidates if c["id"] not in exclude_ids]
        if not candidates:
            # fallback: random from other difficulties
            all_qs = sum([self.bank.get(domain, {}).get(d, []) for d in ["easy","medium","hard"]], [])
            candidates = [c for c in all_qs if c["id"] not in exclude_ids]
            if not candidates:
                raise RuntimeError("No questions available")
        return random.choice(candidates)
