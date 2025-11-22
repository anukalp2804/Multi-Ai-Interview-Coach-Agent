# main.py
from orchestrator_agent import OrchestratorAgent
from pathlib import Path
import time

if __name__ == "__main__":
    ob = OrchestratorAgent(Path("tools/question_bank.json"))
    sid = ob.start_session("demo_user", domain="java")
    q = ob.ask_next(sid, "easy")
    print("Question:", q["q"])
    ans = input("Your answer: ")
    res = ob.submit_answer(sid, ans)
    print("Evaluation:", res)
    q = ob.ask_next(sid, "medium")
    print("Question:", q["q"])
    ans = input("Answer: ")
    res = ob.submit_answer(sid, ans)
    print("Evaluation:", res)
    summary = ob.finish_session(sid)
    print("Summary:", summary)
