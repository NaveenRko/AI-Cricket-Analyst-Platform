import os
from create_db import create_database

# Create database automatically if missing
if not os.path.exists("database/ipl.duckdb"):
    create_database()

import streamlit as st

from langchain_groq import ChatGroq

#from agents.supervisor_agent import decide_agent
# replace with supervisor agent with classifier
from IntentClassifier.predict_intent import predict_intent

from agents.batting_agent import get_batting_result
from agents.bowling_agent import get_bowling_result
from agents.team_agent import get_team_result
from agents.season_agent import get_season_result
from agents.venue_agent import get_venue_result
from agents.matchup_agent import get_matchup_result

from agents.rag_agent import get_rag_answer 
from agents.hybrid_agents import get_hybrid_answer
from agents.rag_hybrid import get_rag_hybrid_answer
from agents.pipeline_router import pipeline_router
from agents.sql_intent_router import sql_intent_router
from agents.search_orchestrator import search_orchestrator

from memory.memory import memory
from memory.memory_agent import rewrite_question

from dotenv import load_dotenv
import os

# for query log tracking
import pandas as pd
import numpy as np
from datetime import datetime
import time

import numpy as np
import math
import traceback

from database.logger import save_feedback_log

# ==================================
# PAGE CONFIG
# ==================================

st.set_page_config(
    page_title="IPL AI Analyst",
    page_icon="🏏",
    layout="wide"
)

st.title("🏏 IPL AI Analyst")

st.write(
    "Ask any IPL analytics question."
)
# ==================================
# SESSION STATE
# ==================================

if "answer" not in st.session_state:
    st.session_state.answer = None

if "query_log_id" not in st.session_state:
    st.session_state.query_log_id = None

if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = False

# ==================================
# LOAD ENV
# ==================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ==================================
# LLM
# ==================================

llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.3-70b-versatile",
    temperature=0
)

# ==================================
# USER INPUT
# ==================================

question = st.text_input(
    "Ask IPL Question"
)

# ==================================
# ANALYZE
# ==================================

if st.button("Analyze"):

    if question:

        with st.spinner("Analyzing IPL Data..."):

            try:

                start_time = time.time()
                # Retrive history (Memory)
                history = memory.load_memory_variables({})

                needs_rewrite = any(
                    word in question.lower()
                    for word in ["he","his","him","she",
                        "her","they","them","that player",
                        "that team","same season","previous"
                    ]
                )
                
                if needs_rewrite:
                    rewritten_question = rewrite_question(
                        llm,
                        history,
                        question
                    )
                else:
                    rewritten_question = question

                from utils.alias_resolver import normalize_question

                rewritten_question = normalize_question(rewritten_question)
                                
                # ---------------------
                # decide agent with calssifier
                
                from IntentClassifier.predict_intent import predict_intent
                
                SQL_AGENT_MAP = {
                
                    "batting": get_batting_result,
                
                    "bowling": get_bowling_result,
                
                    "venue": get_venue_result,
                
                    "season": get_season_result,
                
                    "team": get_team_result,
                
                    "matchup": get_matchup_result
                
                }
                
                prediction = predict_intent(rewritten_question)
                
                intent = prediction["intent"]
                
                confidence = prediction["confidence"]
                
                # -----------------------------
                # HIGH CONFIDENCE
                # -----------------------------
                
                if confidence >= 0.80:
                
                    # -----------------
                    # SQL intents
                    # -----------------
                
                    if intent in SQL_AGENT_MAP:
                
                        pipeline = "sql"
                
                        sql_agent = SQL_AGENT_MAP[intent]
                
                        result = get_hybrid_answer(
                
                            llm,
                
                            rewritten_question,
                
                            sql_agent
                
                        )
                
                    # -----------------
                    # RAG
                    # -----------------
                
                    elif intent == "rag":
                
                        pipeline = "rag"
                
                        result = get_rag_hybrid_answer(
                
                            llm,
                
                            rewritten_question
                
                        )
                
                    # -----------------
                    # Out of scope
                    # -----------------
                
                    elif intent == "out_of_scope":
                
                        pipeline = "out_of_scope"
                
                        result = {
                
                            "answer": "I'm an IPL specialist AI analyst. Please ask IPL-related questions.",
                
                            "generated_sql": None,
                
                            "sql_result": None,
                
                            "sql_error": None,
                
                            "rag_docs": [],
                
                            "tavily_sources": [],
                
                            "search_used": "out_of_scope",
                
                            "llm_calls": 0
                
                        }
                
                    # -----------------
                    # Unexpected label
                    # -----------------
                
                    else:
                
                        route = pipeline_router(
                
                            llm,
                
                            rewritten_question
                
                        )
                
                        pipeline = route["pipeline"]
                
                        intent = None
                
                # -----------------------------
                # LOW CONFIDENCE
                # -----------------------------
                
                if confidence < 0.80:
                
                    route = pipeline_router(
                
                        llm,
                
                        rewritten_question
                
                    )
                
                    pipeline = route["pipeline"]
                
                    if pipeline == "sql":
                
                        sql_route = sql_intent_router(
                
                            llm,
                
                            rewritten_question
                
                        )
                
                        intent = sql_route["intent"]
                
                        sql_agent = SQL_AGENT_MAP[intent]
                
                        result = get_hybrid_answer(
                
                            llm,
                
                            rewritten_question,
                
                            sql_agent
                
                        )
                
                    elif pipeline == "rag":
                
                        intent = "rag"
                
                        result = get_rag_hybrid_answer(
                
                            llm,
                
                            rewritten_question
                
                        )
                
                    elif pipeline == "tavily":
                
                        intent = "tavily"
                
                        result = search_orchestrator(
                
                            llm,
                
                            rewritten_question
                
                        )
                
                    else:
                
                        intent = "out_of_scope"
                
                        result = {
                
                            "answer": "I'm an IPL specialist AI analyst. Please ask IPL-related questions.",
                
                            "generated_sql": None,
                
                            "sql_result": None,
                
                            "sql_error": None,
                
                            "rag_docs": [],
                
                            "tavily_sources": [],
                
                            "search_used": "out_of_scope",
                
                            "llm_calls": 0
                
                        }
                
                final_answer = result["answer"]
            
                # Save conversation (Memory)
                memory.save_context(
                    {"input": question},
                    {"output": final_answer}
                )
                st.subheader(
                    "AI Analysis"
                )

                st.session_state.answer = final_answer

                # ---------------------
                # Latency time
                response_time = round(time.time() - start_time,2)
                # ---------------------
                # Save Logs
                # ---------------------
                
                from database.logger import (
                    save_query,
                    save_sql_log,
                    save_tavily_log
                )
                from database.logger import save_evaluation_log
                
                query_log_id = save_query({
                
                    "question": question,
                
                    "rewritten_question": rewritten_question,
                
                    "agent_selected": intent if intent else pipeline,
                
                    "pipeline": pipeline,
                
                    "status": "success",
                
                    "error_message": None,
                
                    "model_used": "llama-3.3-70b-versatile",
                
                    "final_answer": final_answer,
                
                    "response_time": response_time
                
                })

                st.session_state.query_log_id = query_log_id
                
                save_sql_log(
                
                    query_log_id=query_log_id,
                
                    generated_sql=result.get("generated_sql"),
                
                    sql_result=result.get("sql_result"),
                
                    error=result.get("sql_error")
                
                )
                
                save_tavily_log(
                
                    query_log_id=query_log_id,
                
                    search_used=result.get("search_used"),
                
                    tavily_sources=result.get("tavily_sources", [])
                
                )

                save_evaluation_log(

                    query_log_id=query_log_id,
                
                    pipeline=pipeline,
                
                    status="success" if final_answer else "failed",
                
                    sql_used=result.get("generated_sql") is not None,
                
                    rag_used=len(result.get("rag_docs", [])) > 0,
                
                    tavily_used=result.get("search_used") == "tavily",
                
                    generated_sql=result.get("generated_sql") is not None,
                
                    llm_calls=result.get("llm_calls", 2),
                
                    response_time=response_time,
                
                    intent=intent,
                
                    confidence=confidence
                )
                                            
            except Exception as e:
                response_time = round(
                    time.time() - start_time,
                        2
                    ) if "start_time" in locals() else None
                from database.logger import save_query
                save_query({
                    "question": question if "question" in locals() else None,
                
                    "rewritten_question": rewritten_question
                    if "rewritten_question" in locals()
                    else question,
                
                    "agent_selected": intent
                    if "intent" in locals()
                    else None,
                
                    "pipeline": pipeline
                    if "pipeline" in locals()
                    else None,
                
                    "status": "error",
                
                    "error_message": traceback.format_exc(),
                
                    "model_used": "llama-3.3-70b-versatile",
                
                    "final_answer": None,
                
                    "response_time": response_time
                
                })
                
                st.code(traceback.format_exc())

# ===================================
# Display latest answer
# ===================================

if st.session_state.answer:

    st.write(st.session_state.answer)

if st.session_state.answer:

    st.divider()

    st.write("### Was this answer helpful?")

    col1, col2 = st.columns(2)

    with col1:

        if st.button("👍 Yes"):

            save_feedback_log({

                "query_log_id": st.session_state.query_log_id,

                "feedback": "like",

                "reason": None,

                "comment": None

            })

            st.success("Thanks for your feedback!")

    with col2:

        if st.button("👎 No"):

            st.session_state.show_feedback = True

if st.session_state.show_feedback:

    reason = st.selectbox(
        "Reason",
        [
            "Wrong Statistics",
            "Wrong Intent",
            "Wrong Player",
            "Hallucination",
            "Incomplete Answer",
            "Too Slow",
            "Other"
        ]
    )

    comment = st.text_area("Comments")

    if st.button("Submit Feedback"):

        save_feedback_log({

            "query_log_id": st.session_state.query_log_id,

            "feedback":"dislike",

            "reason":reason,

            "comment":comment

        })

        st.success("Feedback Submitted!")

        st.session_state.show_feedback = False