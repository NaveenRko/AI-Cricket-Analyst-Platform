import os
import time
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def now_ist() -> str:
    return datetime.now(IST).strftime("%I:%M %p")

from create_db import create_database

if not os.path.exists("database/ipl.duckdb"):
    create_database()

import streamlit as st
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from graph_pipeline import build_graph
from memory.memory import memory

from database.logger import (
    save_query, save_sql_log, save_tavily_log,
    save_evaluation_log, save_feedback_log,
)

# ---------------------------------------------------------------------------
# Page config + env + LLM 
# ---------------------------------------------------------------------------
st.set_page_config(page_title="IPL AI Analyst", page_icon="🏏", layout="centered")

load_dotenv()
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

llm = ChatOpenAI(
    api_key=NVIDIA_API_KEY,
    base_url="https://integrate.api.nvidia.com/v1",
    model="openai/gpt-oss-120b",
    temperature=0,
    timeout=45,       # fail fast instead of the openai SDK's 600s default;
                      # 45s (not 30s) since this is now only tier-2 fallback
                      # for SQL and the main path for rag/tavily/comparator
    max_retries=1,    # 1 retry, not the default 2 (each with backoff)
)

# gpt-oss-120b is a REASONING model (see build.nvidia.com/openai/gpt-oss-120b:
# "Mixture of Experts (MoE) reasoning LLM") — it generates a hidden internal
# chain-of-thought before every answer, which is what made your responses
# deeper than the old Llama model but also what's driving latency, since the
# router now calls SOME model on every single message before an answer is
# even started. Routing is pure JSON classification — it gains nothing from
# reasoning depth — so it gets a fast, non-reasoning model instead. The
# actual answer-generating nodes (sql/rag/tavily/comparator) keep using the
# reasoning `llm` above, since that's where the quality improvement you
# noticed actually lives.
#
# NVIDIA's free tier keeps rotating which models get pulled from the Free
# Endpoint tier (llama-3.3-70b-instruct and llama-3.1-8b-instruct have both
# been cycled/deprecated within days of each other). Rather than hardcoding
# one model that can silently die again, this chains several free,
# non-reasoning NVIDIA endpoints with LangChain's built-in `.with_fallbacks`:
# if the primary model errors (quota, deprecation, downtime), it transparently
# retries the same request on the next one in the list. No code elsewhere
# needs to change — `fast_llm` is still a normal Runnable.
def _fast_candidate(model_name: str, timeout: int = 15) -> ChatOpenAI:
    return ChatOpenAI(
        api_key=NVIDIA_API_KEY,
        base_url="https://integrate.api.nvidia.com/v1",
        model=model_name,
        temperature=0,
        timeout=timeout,
        max_retries=0,  # let with_fallbacks() move to the next model instead
    )


fast_llm = _fast_candidate("nvidia/nemotron-mini-4b-instruct").with_fallbacks([
    _fast_candidate("meta/llama-3.2-3b-instruct"),
    _fast_candidate("qwen/qwen2-7b-instruct"),
])

# ---------------------------------------------------------------------------
# WhatsApp visual chrome
# ---------------------------------------------------------------------------
TEAL_HEADER, BUBBLE_OUT, BUBBLE_IN = "#075E54", "#DCF8C6", "#FFFFFF"
CHAT_BG, TEXT_MUTED, CHECK_BLUE = "#ECE5DD", "#667781", "#53BDEB"

st.markdown(f"""
<style>
    #MainMenu, footer, header {{visibility: hidden;}}
    .block-container {{ padding: 0 !important; max-width: 480px; margin: 0 auto; }}
    .stApp {{ background: {CHAT_BG}; }}
    .wa-header {{
        background: {TEAL_HEADER}; color: white; padding: 14px 16px;
        display: flex; align-items: center; gap: 12px;
        position: sticky; top: 0; z-index: 999;
        font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
    }}
    .wa-avatar {{
        width: 40px; height: 40px; border-radius: 50%; background: #128C7E;
        display: flex; align-items: center; justify-content: center;
        font-weight: 600; font-size: 16px; color: white; flex-shrink: 0;
    }}
    .wa-header-name {{ font-size: 16px; font-weight: 600; }}
    .wa-header-status {{ font-size: 12.5px; color: #d4f5ec; }}
    .wa-chat {{ padding: 14px 10px 10px 10px; font-family: -apple-system,"Segoe UI",Helvetica,Arial,sans-serif; }}
    .wa-row {{ display: flex; margin-bottom: 4px; }}
    .wa-row.out {{ justify-content: flex-end; }}
    .wa-row.in {{ justify-content: flex-start; }}
    .wa-bubble {{
        max-width: 82%; padding: 7px 9px 6px 9px; border-radius: 8px;
        font-size: 14.5px; line-height: 1.4; color: #111B21;
        box-shadow: 0 1px 0.5px rgba(0,0,0,0.13); word-wrap: break-word; white-space: pre-wrap;
    }}
    .wa-bubble.out {{ background: {BUBBLE_OUT}; border-top-right-radius: 0; }}
    .wa-bubble.in {{ background: {BUBBLE_IN}; border-top-left-radius: 0; }}
    .wa-meta {{ display: flex; justify-content: flex-end; gap: 3px; margin-top: 2px; font-size: 11px; color: {TEXT_MUTED}; }}
    .wa-check {{ color: {CHECK_BLUE}; font-size: 13px; }}
    .wa-pipeline-tag {{
        margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(0,0,0,0.08);
        font-size: 11px; color: {TEXT_MUTED};
    }}
    div[data-testid="stChatInput"] {{ max-width: 480px; margin: 0 auto; background: #F0F0F0; border-top: 1px solid #d9d9d9; }}
    div[data-testid="stChatInput"] textarea {{ background: white !important; border-radius: 20px !important; }}

    /* compact feedback row directly under each assistant bubble */
    div[data-testid="stHorizontalBlock"] {{
        margin-top: -14px; margin-bottom: 6px; gap: 0.25rem; max-width: 140px;
    }}
    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {{
        padding: 1px 8px; font-size: 12px; min-height: 26px; line-height: 1.2;
    }}
    .element-container {{ margin-bottom: 0 !important; }}
</style>
""", unsafe_allow_html=True)


def render_bubble(text: str, time_str: str, is_out: bool, tag_html: str = "") -> None:
    """Renders one chat bubble as a single-line HTML string.

    Must stay single-line / unindented: Streamlit's markdown renderer treats
    any line indented 4+ spaces as a code block, which is what happens if this
    HTML is built as a multi-line f-string inside a for-loop (inherits Python
    indentation) — that's why the raw <div class="wa-meta">...</div> was
    showing up as literal text instead of rendering.
    """
    row_cls = "out" if is_out else "in"
    ticks = '<span class="wa-check">✓✓</span>' if is_out else ""
    html = (
        f'<div class="wa-row {row_cls}"><div class="wa-bubble {row_cls}">'
        f'{text}{tag_html}'
        f'<div class="wa-meta">{time_str} {ticks}</div>'
        f'</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)

st.markdown("""
<div class="wa-header">
    <div class="wa-avatar">🏏</div>
    <div>
        <div class="wa-header-name">IPL AI Analyst</div>
        <div class="wa-header-status">online</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state — one running thread instead of a single answer slot
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "text": "Ask me any IPL analytics question — batting, bowling, venues, matchups, records.",
         "time": now_ist(), "pipeline": None, "query_log_id": None,
         "feedback_given": True},  # greeting has nothing to log feedback against
    ]

# ---------------------------------------------------------------------------
# Core pipeline call — same logic as app.py's Analyze block, just wrapped
# ---------------------------------------------------------------------------
compiled_graph = build_graph(llm, fast_llm)


def run_pipeline(question: str) -> dict:
    start_time = time.time()

    # Single LangGraph invocation now handles: pronoun rewrite, smalltalk,
    # out-of-scope/injection detection, pipeline choice, sql sub-intent, and
    # (for multi-entity comparisons) fanning out one lookup per entity and
    # synthesizing the final comparison. No classifier, no separate
    # pipeline_router/sql_intent_router calls.
    final_state = compiled_graph.invoke({"question": question})

    final_answer = final_state["final_answer"]
    pipeline = final_state.get("pipeline")
    intent = final_state.get("intent")
    result = final_state.get("result", {}) or {}
    rewritten_question = final_state.get("rewritten_question", question)

    memory.save_context({"input": question}, {"output": final_answer})

    response_time = round(time.time() - start_time, 2)

    query_log_id = save_query({
        "question": question, "rewritten_question": rewritten_question,
        "agent_selected": intent if intent else pipeline, "pipeline": pipeline,
        "status": "success", "error_message": None,
        "model_used": "openai/gpt-oss-120b",
        "final_answer": final_answer, "response_time": response_time,
    })

    save_sql_log(query_log_id=query_log_id, generated_sql=result.get("generated_sql"),
                 sql_result=result.get("sql_result"), error=result.get("sql_error"))
    save_tavily_log(query_log_id=query_log_id, search_used=result.get("search_used"),
                     tavily_sources=result.get("tavily_sources", []))
    save_evaluation_log(
        query_log_id=query_log_id, pipeline=pipeline, status="success" if final_answer else "failed",
        sql_used=result.get("generated_sql") is not None,
        rag_used=len(result.get("rag_docs", [])) > 0,
        tavily_used=result.get("search_used") == "tavily",
        generated_sql=result.get("generated_sql") is not None,
        llm_calls=result.get("llm_calls", 2), response_time=response_time,
        intent=intent, confidence=1.0,
    )

    return {"answer": final_answer, "pipeline": pipeline, "intent": intent,
            "query_log_id": query_log_id, "confidence": 1.0}


# ---------------------------------------------------------------------------
# Render the thread
# ---------------------------------------------------------------------------
st.markdown('<div class="wa-chat">', unsafe_allow_html=True)

for i, msg in enumerate(st.session_state.messages):
    is_out = msg["role"] == "user"
    tag = (
        f'<div class="wa-pipeline-tag">via {msg["pipeline"]}'
        f'{" · " + msg["intent"] if msg.get("intent") else ""}</div>'
        if (not is_out and msg.get("pipeline")) else ""
    )
    render_bubble(msg["text"], msg["time"], is_out, tag)

    # feedback controls per assistant answer (native widgets, can't be pure HTML)
    if not is_out and not msg.get("feedback_given") and msg.get("query_log_id"):
        c1, c2 = st.columns([1, 1])
        if c1.button("👍", key=f"up_{i}"):
            save_feedback_log({"query_log_id": msg["query_log_id"], "feedback": "like",
                                "reason": None, "comment": None})
            st.session_state.messages[i]["feedback_given"] = True
            st.rerun()
        if c2.button("👎", key=f"down_{i}"):
            st.session_state.messages[i]["show_feedback_form"] = True

        if msg.get("show_feedback_form"):
            reason = st.selectbox(
                "Reason", ["Wrong Statistics", "Wrong Intent", "Wrong Player",
                           "Hallucination", "Incomplete Answer", "Too Slow", "Other"],
                key=f"reason_{i}",
            )
            comment = st.text_area("Comments", key=f"comment_{i}")
            if st.button("Submit Feedback", key=f"submit_{i}"):
                save_feedback_log({"query_log_id": msg["query_log_id"], "feedback": "dislike",
                                    "reason": reason, "comment": comment})
                st.session_state.messages[i]["feedback_given"] = True
                st.session_state.messages[i]["show_feedback_form"] = False
                st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------
question = st.chat_input("Ask an IPL question")

if question:
    st.session_state.messages.append({
        "role": "user", "text": question,
        "time": now_ist(),
    })

    with st.spinner("Analyzing IPL data..."):
        try:
            result = run_pipeline(question)
            st.session_state.messages.append({
                "role": "assistant", "text": result["answer"],
                "time": now_ist(),
                "pipeline": result["pipeline"], "intent": result["intent"],
                "query_log_id": result["query_log_id"], "feedback_given": False,
            })
        except Exception:
            error_text = traceback.format_exc()
            save_query({
                "question": question, "rewritten_question": question,
                "agent_selected": None, "pipeline": None, "status": "error",
                "error_message": error_text, "model_used": "openai/gpt-oss-120b",
                "final_answer": None, "response_time": None,
            })
            st.session_state.messages.append({
                "role": "assistant", "text": f"Something went wrong:\n\n{error_text[-400:]}",
                "time": now_ist(),
                "pipeline": "error", "intent": None, "query_log_id": None, "feedback_given": True,
            })

    st.rerun()