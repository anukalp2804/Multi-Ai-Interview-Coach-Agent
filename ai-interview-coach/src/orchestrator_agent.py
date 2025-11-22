# orchestrator_agent.py
from pathlib import Path
from interviewer_agent import InterviewerAgent
from evaluator_agent import EvaluatorAgent
from memory_agent import MemoryAgent
from a2a_bus import A2ABus
from utils import logger

class OrchestratorAgent:
    def __init__(self, question_bank_path: Path, llm_adapter: str = None):
        self.bus = A2ABus()
        self.interviewer = InterviewerAgent(question_bank_path)
        self.evaluator = EvaluatorAgent(llm_adapter)
        # MemoryAgent will create/open DB at storage/interview_sessions.db by default
        self.memory = MemoryAgent()
        self.active_sessions = {}  # session_id -> state

    def start_session(self, user_id: str, domain: str = "java"):
        # create session id and initialize memory
        session_id = self.memory.create_session(user_id)
        # also set domain explicitly
        self.memory.start_session(session_id, user_id, domain)
        # orchestrator-local state
        state = {
            "session_id": session_id,
            "user_id": user_id,
            "domain": domain,
            "questions_asked": [],
            "current_q": None,
            "paused": False,
            "scores": []
        }
        self.active_sessions[session_id] = state
        logger.info(f"Started session {session_id} for user {user_id} domain {domain}")
        # broadcast
        self.bus.publish("session_started", {"session_id": session_id, "user_id": user_id, "domain": domain})
        return session_id

    def ask_next(self, session_id: str, difficulty: str):
        state = self.active_sessions.get(session_id)
        if not state:
            raise RuntimeError("Session not found")
        exclude = [q.get("id") for q in state["questions_asked"]]
        q = self.interviewer.pick_question(state["domain"], difficulty, exclude)
        state["current_q"] = q
        state["questions_asked"].append(q)
        self.bus.publish("question_asked", {"session_id": session_id, "question": q})
        return q

    def submit_answer(self, session_id: str, answer_text: str):
        state = self.active_sessions.get(session_id)
        if not state:
            raise RuntimeError("Session not found")
        q = state.get("current_q")
        if not q:
            raise RuntimeError("No current question")
        # evaluate with evaluator (evaluator expects question dict + user answer)
        eval_result = self.evaluator.evaluate(q, answer_text)
        # update orchestrator state
        state["scores"].append(eval_result.get("score", 0))
        # record to memory
        self.memory.add_interaction(session_id, q, eval_result)
        # broadcast evaluation
        self.bus.publish("answer_evaluated", {
            "session_id": session_id, "question": q, "answer": answer_text, "evaluation": eval_result
        })
        # clear current question
        state["current_q"] = None
        return eval_result

    def pause_session(self, session_id: str):
        s = self.active_sessions.get(session_id)
        if s:
            s["paused"] = True
            self.bus.publish("session_paused", {"session_id": session_id})

    def resume_session(self, session_id: str):
        s = self.active_sessions.get(session_id)
        if s:
            s["paused"] = False
            self.bus.publish("session_resumed", {"session_id": session_id})

    def finish_session(self, session_id: str):
        # Build rich summary from MemoryAgent sessions data (not just scores)
        sess = self.memory.sessions.get(session_id)
        if not sess:
            # if memory persisted earlier, try loading
            loaded = self.memory.load_session(session_id)
            sess = loaded or {}
        # Build details list
        details = []
        scores = []
        history = sess.get("history", [])
        for entry in history:
            q = entry.get("question", {})
            ev = entry.get("evaluation", {})
            scores.append(ev.get("score", 0))
            details.append({
                "question_id": q.get("id"),
                "question": q.get("q"),
                "correct_answer": q.get("answer"),
                "score": ev.get("score"),
                "feedback": ev.get("feedback"),
                "suggestions": ev.get("suggestions", [])
            })
        average = round(sum(scores) / len(scores), 2) if scores else 0.0

        summary = {
            "student": sess.get("user_id"),
            "domain": sess.get("domain"),
            "num_questions": len(scores),
            "average_score": average,
            "details": details,
            "weaknesses": sess.get("weaknesses", {})
        }

        # persist to DB
        try:
            self.memory.persist_session(session_id)
        except Exception as e:
            logger.exception("Failed to persist session: %s", e)

        # broadcast
        self.bus.publish("session_finished", {"session_id": session_id, "summary": summary})

        # remove from active sessions if present
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

        return summary
