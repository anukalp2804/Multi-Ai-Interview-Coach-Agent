# app.py — FINAL VERSION (LIVE AUT0-REFRESH TIMER + AUTO-TIMEOUT + NO VOICE)
import streamlit as st
from pathlib import Path
from streamlit_autorefresh import st_autorefresh

from orchestrator_agent import OrchestratorAgent

# ------------------------------------
# STREAMLIT CONFIG
# ------------------------------------
st.set_page_config(page_title="AI Interview Coach — Final", layout="wide")

# ------------------------------------
# LOAD ORCHESTRATOR (SINGLETON)
# ------------------------------------
if "orch" not in st.session_state:
    st.session_state["orch"] = OrchestratorAgent(Path("tools/question_bank.json"))
orch = st.session_state["orch"]

# ------------------------------------
# SESSION STATE DEFAULTS
# ------------------------------------
defaults = {
    "session_id": None,
    "current_q": None,
    "flow_index": 0,
    "difficulty_flow": ["easy", "medium", "hard"],
    "last_evaluation": None,
    "username": "student1",
    "domain": "java",
    "session_summary": None,
    "timer": 20,
    "timer_expired": False,
    "timer_running": False,  # NEW FLAG
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ------------------------------------
# HEADER
# ------------------------------------
st.title("Multi-Agent Interview Coach")
st.write("Timer is LIVE and auto-submits when it reaches 0.")

# ------------------------------------
# SIDEBAR
# ------------------------------------
with st.sidebar:
    st.header("Session Controls")
    st.session_state["username"] = st.text_input("Your Name", st.session_state["username"])
    st.session_state["domain"] = st.selectbox(
        "Domain", ["java", "python", "dsa"],
        index=["java", "python", "dsa"].index(st.session_state["domain"])
    )

    if st.button("Start Session"):
        sid = orch.start_session(st.session_state["username"], st.session_state["domain"])
        st.session_state["session_id"] = sid
        st.session_state["flow_index"] = 0
        st.session_state["current_q"] = None
        st.session_state["last_evaluation"] = None
        st.session_state["session_summary"] = None
        st.session_state["timer"] = 20
        st.session_state["timer_expired"] = False
        st.session_state["timer_running"] = False
        st.success(f"Session started for {st.session_state['username']}")
        st.rerun()

    if st.button("Finish Session"):
        if st.session_state["session_id"]:
            summary = orch.finish_session(st.session_state["session_id"])
            st.session_state["session_summary"] = summary
            st.session_state["session_id"] = None
            st.session_state["current_q"] = None
            st.session_state["flow_index"] = 0
            st.session_state["last_evaluation"] = None
            st.session_state["timer_running"] = False
            st.success("Session finished — summary below.")

st.markdown("---")

# ------------------------------------
# MAIN LAYOUT
# ------------------------------------
col_main, col_side = st.columns([3, 1])

# ======================================================================
# MAIN INTERVIEW AREA
# ======================================================================
with col_main:
    st.subheader("Interviewer")

    if st.session_state["session_id"]:

        # Load next question if needed
        if st.session_state["current_q"] is None:
            if st.session_state["flow_index"] < len(st.session_state["difficulty_flow"]):
                difficulty = st.session_state["difficulty_flow"][st.session_state["flow_index"]]
                q = orch.ask_next(st.session_state["session_id"], difficulty)
                st.session_state["current_q"] = q
                st.session_state["timer"] = 20
                st.session_state["timer_running"] = True
                st.session_state["timer_expired"] = False
            else:
                st.info("Questions completed. Click Finish Session.")
                st.stop()

        q = st.session_state["current_q"]
        difficulty = st.session_state["difficulty_flow"][st.session_state["flow_index"]]

        # Difficulty badge
        colors = {"easy": "#4CAF50", "medium": "#FFC107", "hard": "#F44336"}
        icons = {"easy": "🟢 EASY", "medium": "🟡 MEDIUM", "hard": "🔴 HARD"}
        st.markdown(
            f"<span style='background:{colors[difficulty]};color:white;padding:6px 14px;"
            f"border-radius:8px;font-weight:bold;'>{icons[difficulty]}</span>",
            unsafe_allow_html=True
        )

        st.write(f"### {q.get('q')}")

        # ---------------------------------------------------------------------
        # LIVE AUTO-REFRESH TIMER (THIS IS WHAT MAKES IT COUNT DOWN!!)
        # ---------------------------------------------------------------------
        if st.session_state["timer_running"]:
            st_autorefresh(interval=1000, key="refresh_timer")

            # Decrease timer each refresh
            if st.session_state["timer"] > 0:
                st.session_state["timer"] -= 1
            else:
                st.session_state["timer_expired"] = True

        # Display timer
        st.markdown(
            f"<h2 style='font-weight:bold;'>⏳ {st.session_state['timer']}s</h2>",
            unsafe_allow_html=True
        )

        # Auto-submit when timer hits 0
        if st.session_state["timer_expired"]:
            st.info("⏱ Time's up! Auto-submitting answer…")
            eval_res = orch.submit_answer(st.session_state["session_id"], "TIMEOUT")
            st.session_state["last_evaluation"] = eval_res
            st.session_state["flow_index"] += 1
            st.session_state["current_q"] = None
            st.session_state["timer"] = 20
            st.session_state["timer_expired"] = False
            st.session_state["timer_running"] = False
            st.rerun()

        # -------------------------------
        # Text Answer Box
        # -------------------------------
        answer_key = f"ans_{st.session_state['flow_index']}"
        user_answer = st.text_area("Your answer:", key=answer_key)

        # -------------------------------
        # Manual Submit
        # -------------------------------
        if st.button("Submit Answer"):
            eval_res = orch.submit_answer(st.session_state["session_id"], user_answer)
            st.session_state["last_evaluation"] = eval_res

            st.write("### Evaluation")
            st.write(f"Score: {eval_res.get('score')}/10")
            st.write("Feedback:", eval_res.get("feedback"))
            if eval_res.get("suggestions"):
                st.write("Suggestions:")
                for s in eval_res["suggestions"]:
                    st.write("-", s)

            # Show correct answer
            st.success(q.get("answer"))

            # Move to next question
            st.session_state["flow_index"] += 1
            st.session_state["current_q"] = None
            st.session_state["timer_running"] = False

    else:
        st.info("Start a session to begin.")

# ======================================================================
# SIDE PANEL
# ======================================================================
with col_side:
    st.subheader("Session Info")
    st.write("👤 Name:", st.session_state["username"])
    st.write("📘 Domain:", st.session_state["domain"])
    st.write("🔢 Question #:", st.session_state["flow_index"])

    if st.session_state["last_evaluation"]:
        ev = st.session_state["last_evaluation"]
        st.metric("Last Score", f"{ev.get('score')}/10")
        st.write("Feedback:", ev.get("feedback"))

# ======================================================================
# SUMMARY
# ======================================================================
if st.session_state.get("session_summary"):
    st.markdown("---")
    st.subheader("Session Summary")
    with st.expander("Expand Summary", expanded=True):
        st.json(st.session_state["session_summary"])
