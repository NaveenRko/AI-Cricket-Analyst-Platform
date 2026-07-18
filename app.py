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
                    result = get_hybrid_answer(
                        llm,
                        question,
                        sql_result_function
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
                from database.logger import save_query
                from database.logger import save_sql_log
                from database.logger import save_tavily_log

                query_log_id = save_query({
                    "question": question,
                
                    "rewritten_question": rewritten_question,
                
                    "agent_selected": agent_type,
                
                    "final_answer": final_answer,
                
                    "response_time": response_time
                
                })
                save_sql_log(

                    query_log_id=query_log_id,
                
                    generated_sql=result["generated_sql"],
                
                    sql_result=result["sql_result"],
                
                    error=result.get("sql_error")
                
                )
                save_tavily_log(

                    query_log_id=query_log_id,
                
                    search_used=result.get("search_used"),
                
                    tavily_sources=result.get("tavily_sources", [])
                
                )

            except Exception as e:

                st.error(
                    f"Error: {str(e)}"
                )