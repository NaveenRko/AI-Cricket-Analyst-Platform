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

from agents.batting_agent import get_batting_agent
from agents.bowling_agent import get_bowling_agent
from agents.venue_agent import get_venue_agent
from agents.matchup_agent import get_matchup_agent
from agents.team_agent import get_team_agent
from agents.season_agent import get_season_agent
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
# LOAD AGENTS
# ==================================

batting_agent = get_batting_agent(llm)
bowling_agent = get_bowling_agent(llm)
venue_agent = get_venue_agent(llm)
matchup_agent = get_matchup_agent(llm)
team_agent = get_team_agent(llm)
season_agent = get_season_agent(llm)


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

                rewritten_question = rewrite_question(
                    llm,
                    history,
                    question
                )
                
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
                        batting_agent
                    )
                
                    final_answer = result["answer"]
                
                    retrieved_docs = result["rag_docs"]
                
                
                elif agent_type == "bowling":
                
                    result = get_hybrid_answer(
                        llm,
                        rewritten_question,
                        bowling_agent
                    )
                
                    final_answer = result["answer"]
                
                    retrieved_docs = result["rag_docs"]
                
                
                elif agent_type == "venue":
                
                    result = get_hybrid_answer(
                        llm,
                        rewritten_question,
                        venue_agent
                    )
                
                    final_answer = result["answer"]
                
                    retrieved_docs = result["rag_docs"]
                
                
                elif agent_type == "matchup":
                
                    result = get_hybrid_answer(
                        llm,
                        rewritten_question,
                        matchup_agent
                    )
                
                    final_answer = result["answer"]
                
                    retrieved_docs = result["rag_docs"]
                
                
                elif agent_type == "team":
                
                    result = get_hybrid_answer(
                        llm,
                        rewritten_question,
                        team_agent
                    )
                
                    final_answer = result["answer"]
                
                    retrieved_docs = result["rag_docs"]
                
                
                elif agent_type == "season":
                
                    result = get_hybrid_answer(
                        llm,
                        rewritten_question,
                        season_agent
                    )
                
                    final_answer = result["answer"]
                
                    retrieved_docs = result["rag_docs"]
                
                
                elif agent_type == "rag":
                
                    result = get_rag_answer(
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

            except Exception as e:

                st.error(
                    f"Error: {str(e)}"
                )