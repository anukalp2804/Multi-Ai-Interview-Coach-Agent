# memory_agent.py
import time
import uuid
import json
from pathlib import Path
from typing import Dict, Any
from storage.sqlite_store import SQLiteStore

class MemoryAgent:
    """
    Backwards-compatible MemoryAgent.
    - create_session(user_id) -> session_id (UUID)
    - start_session(session_id, user_id, domain)
    - add_interaction(session_id, question_entry, response)
    - record_answer(session_id, question, evaluation)  # alias
    - persist_session(session_id)
    - load_user_profile(user_id) / save_user_profile(user_id, profile)
    """

    def __init__(self, db_path: Path = None):
        if db_path is None:
            db_path = Path("storage/interview_sessions.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Thread-safe SQLite store (uses new connection per call)
        self.store = SQLiteStore(db_path)

        # In-memory active sessions
        # structure: { session_id: {user_id, domain, created_at, history: [...], weaknesses: {...} } }
        self.sessions: Dict[str, Dict[str, Any]] = {}

    # ------------------------------
    # Session lifecycle helpers
    # ------------------------------
    def create_session(self, user_id: str) -> str:
        """
        Create a new session id and initialize memory for it.
        Returns the session_id (string).
        """
        sid = str(uuid.uuid4())
        # default domain unknown until orchestrator sets/start_session may set domain
        self.sessions[sid] = {
            "user_id": user_id,
            "domain": None,
            "created_at": time.time(),
            "history": [],
            "weaknesses": {}
        }
        return sid

    def start_session(self, session_id: str, user_id: str, domain: str = None):
        """
        Initialize a session object (if not already created).
        This is useful when Orchestrator wants to explicitly start a session.
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "user_id": user_id,
                "domain": domain,
                "created_at": time.time(),
                "history": [],
                "weaknesses": {}
            }
        else:
            self.sessions[session_id]["user_id"] = user_id
            self.sessions[session_id]["domain"] = domain

    # ------------------------------
    # Recording interactions
    # ------------------------------
    def add_interaction(self, session_id: str, question_entry: Dict[str, Any], response: Dict[str, Any]):
        """
        Called by orchestrator when an answer is evaluated.
        Stores question + evaluation in session history and updates weaknesses.
        """
        sess = self.sessions.get(session_id)
        if sess is None:
            raise KeyError(f"Session not found: {session_id}")

        entry = {
            "time": time.time(),
            "question": {
                "id": question_entry.get("id"),
                "q": question_entry.get("q"),
                "answer": question_entry.get("answer", "")
            },
            "evaluation": response
        }
        sess["history"].append(entry)

        # update weaknesses (simple heuristic: score < 6 considered weakness)
        score = int(response.get("score", 0))
        qid = question_entry.get("id")
        if score < 6 and qid:
            sess["weaknesses"].setdefault(qid, 0)
            sess["weaknesses"][qid] += 1

    # alias for older code naming
    def record_answer(self, session_id: str, question: Dict[str, Any], evaluation: Dict[str, Any]):
        self.add_interaction(session_id, question, evaluation)

    # ------------------------------
    # Persistence
    # ------------------------------
    def persist_session(self, session_id: str):
        """
        Serialize the session safely to JSON and save to SQLite.
        """
        sess = self.sessions.get(session_id)
        if not sess:
            return
        try:
            safe_sess = json.loads(json.dumps(sess, default=str))
        except Exception:
            safe_sess = {
                "user_id": sess.get("user_id"),
                "domain": sess.get("domain"),
                "history": [],
                "weaknesses": sess.get("weaknesses", {})
            }
        # Use SQLiteStore.save_session(session_id, user_id, data)
        self.store.save_session(session_id, sess.get("user_id", "unknown"), safe_sess)

    def load_session(self, session_id: str):
        """
        Load a persisted session from storage into memory and return it.
        """
        data = self.store.load_session(session_id)
        if data:
            self.sessions[session_id] = data
        return data

    # ------------------------------
    # User profile helpers (lightweight)
    # ------------------------------
    def load_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Load profile stored under a special session key 'profile_<user_id>'.
        """
        profile_sid = f"profile_{user_id}"
        data = self.store.load_session(profile_sid)
        return data or {}

    def save_user_profile(self, user_id: str, profile: Dict[str, Any]):
        profile_sid = f"profile_{user_id}"
        safe_profile = json.loads(json.dumps(profile, default=str))
        # store as a session row with the profile key
        self.store.save_session(profile_sid, user_id, safe_profile)
