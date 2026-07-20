import os
from create_db import create_database

# Create database automatically if missing
if not os.path.exists("database/ipl.duckdb"):
    create_database()

import streamlit as st

from langchain_groq import ChatGroq

#from agents.router import route_query
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

from memory.memory import memory
from memory.memory_agent import rewrite_question

from dotenv import load_dotenv
import os

# for query log tracking
import pandas as pd
import numpy as np
from datetime import datetime
import time

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
                # ROUTE QUERY
                # ---------------------

                # decide agent type with supervisor
                # agent_type = decide_agent(
                  #  llm,
                   # rewritten_question
                #)
                # decide agent with calssifier
                agent_type = predict_intent(rewritten_question)
                
                retrieved_docs = []
                
                if agent_type == "batting":
                
                    result = get_hybrid_answer(
                        llm,
                        rewritten_question,
                        get_batting_result
                    )
                    
                    final_answer = result["answer"]
                
                    retrieved_docs = result["rag_docs"]
                
                
                elif agent_type == "bowling":
                
                    result = get_hybrid_answer(
                        llm,
                        rewritten_question,
                        get_bowling_result
                    )
                
                    final_answer = result["answer"]
                
                    retrieved_docs = result["rag_docs"]
                
                
                elif agent_type == "venue":
                
                    result = get_hybrid_answer(
                        llm,
                        rewritten_question,
                        get_venue_result
                    )
                
                    final_answer = result["answer"]
                
                    retrieved_docs = result["rag_docs"]
                
                
                elif agent_type == "matchup":
                
                    result = get_hybrid_answer(
                        llm,
                        rewritten_question,
                        get_matchup_result
                    )
                
                    final_answer = result["answer"]
                
                    retrieved_docs = result["rag_docs"]
                
                
                elif agent_type == "team":
                
                    result = get_hybrid_answer(
                        llm,
                        rewritten_question,
                        get_team_result
                    )
                
                    final_answer = result["answer"]
                
                    retrieved_docs = result["rag_docs"]
                
                
                elif agent_type == "season":
                
                    result = get_hybrid_answer(
                        llm,
                        rewritten_question,
                        get_season_result
                    )
                
                    final_answer = result["answer"]
                
                    retrieved_docs = result["rag_docs"]
                
                
                elif agent_type == "rag":

                    result = get_rag_hybrid_answer(
                
                        llm,
                
                        rewritten_question
                
                    )
                
                    final_answer = result["answer"]
                
                    retrieved_docs = result["rag_docs"]        
                else:
                
                    final_answer = (
                        "I am an IPL specialist AI analyst. "
                        "Please ask IPL-related questions."
                    )
                
                    retrieved_docs = []
                # Save conversation (Memory)
                memory.save_context(
                    {"input": question},
                    {"output": final_answer}
                )
                st.subheader(
                    "AI Analysis"
                )

                st.write(
                    final_answer
                )

                # ---------------------
                # Latency time
                response_time = round(time.time() - start_time,2)

                os.makedirs("logs", exist_ok=True)
                
                log = pd.DataFrame([{
                    "timestamp": datetime.now(),
                    "question": question,               
                    "rewritten_question": rewritten_question,                
                    "agent_selected": agent_type,               
                    "rag_sources": ", ".join(retrieved_docs),              
                    "final_answer": final_answer,                
                    "response_time": response_time
                
                }])
                
                file_exists = os.path.exists(
                    "logs/query_logs.csv"
                )
                
                log.to_csv(
                    "logs/query_logs.csv",                
                    mode="a",                
                    header=not file_exists,                
                    index=False                
                )

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
                
                    "agent_selected": agent_type,
                
                    "pipeline": result.get("search_used"),
                
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
                
                    pipeline=result.get("search_used"),
                
                    status="success" if final_answer else "failed",
                
                    sql_used=result.get("generated_sql") is not None,
                
                    rag_used=len(result.get("rag_docs", [])) > 0,
                
                    tavily_used=result.get("search_used") == "tavily",
                
                    generated_sql=result.get("generated_sql") is not None,
                
                    llm_calls=result.get("llm_calls", 2),
                
                    response_time=response_time,
                
                    intent=agent_type,
                
                    confidence=None
                )
                #feedback
                st.subheader("AI Analysis")

                st.write(final_answer)
                
                st.divider()
                
                st.write("### Was this answer helpful?")
                
                col1, col2 = st.columns(2)
                
                with col1:
                
                    if st.button("👍 Yes"):
                
                        from database.logger import save_feedback_log
                
                        save_feedback_log({
                
                            "query_log_id": st.session_state.query_log_id,
                
                            "feedback": "like",
                
                            "reason": None,
                
                            "comment": None
                
                        })
                
                        st.success("Thank you!")
                
                with col2:
                
                    if st.button("👎 No"):
                
                        st.session_state.show_feedback = True
                
                
                if st.session_state.show_feedback:
                
                    reason = st.selectbox(
                
                        "Why wasn't this helpful?",
                
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
                
                    comment = st.text_area(
                
                        "Additional Comments"
                
                    )
                
                    if st.button("Submit Feedback"):
                
                        from database.logger import save_feedback_log
                
                        save_feedback_log({
                
                            "query_log_id": st.session_state.query_log_id,
                
                            "feedback": "dislike",
                
                            "reason": reason,
                
                            "comment": comment
                
                        })
                
                        st.success("Feedback Submitted!")
                
                        st.session_state.show_feedback = False                            
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
            
                    "agent_selected": agent_type
                    if "agent_type" in locals()
                    else None,
            
                    "pipeline": None,
            
                    "status": "error",
            
                    "error_message": str(e),
            
                    "model_used": "llama-3.3-70b-versatile",
            
                    "final_answer": None,
            
                    "response_time": response_time
            
                })
            
                st.error(
                    f"Error: {str(e)}"
                )