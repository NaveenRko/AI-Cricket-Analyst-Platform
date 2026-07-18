import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


import streamlit as st
import pandas as pd

from evaluation.supabase_reader import get_query_logs,get_sql_logs,get_tavily_logs

from evaluation.metrics import calculate_metrics


st.set_page_config(

    page_title="IPL AI Evaluation Dashboard",

    page_icon="📊",

    layout="wide"

)

st.title("📊 IPL AI Evaluation Dashboard")

# --------------------------------
# Load Data
# --------------------------------

query_logs = get_query_logs()

sql_logs = get_sql_logs()

tavily_logs = get_tavily_logs()

metrics = calculate_metrics(query_logs)

# --------------------------------
# KPI Cards
# --------------------------------

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(

        "Total Queries",

        metrics["total_queries"]

    )

with col2:

    st.metric(

        "Average Latency",

        f'{metrics["avg_latency"]} sec'

    )

with col3:

    st.metric(

        "Success Rate",

        f'{metrics["success_rate"]}%'

    )

col4, col5, col6 = st.columns(3)

with col4:

    st.metric(

        "SQL Queries",

        metrics["sql_queries"]

    )

with col5:

    st.metric(

        "FAISS Queries",

        metrics["rag_queries"]

    )

with col6:

    st.metric(

        "Tavily Queries",

        metrics["tavily_queries"]

    )

# --------------------------------
# Query Logs
# --------------------------------

st.divider()

st.subheader("Recent Query Logs")

query_df = pd.DataFrame(query_logs)

st.dataframe(

    query_df,

    use_container_width=True,

    hide_index=True

)

# --------------------------------
# SQL Logs
# --------------------------------

st.divider()

st.subheader("SQL Logs")

sql_df = pd.DataFrame(sql_logs)

st.dataframe(

    sql_df,

    use_container_width=True,

    hide_index=True

)

# --------------------------------
# Tavily Logs
# --------------------------------

st.divider()

st.subheader("Tavily Logs")

tavily_df = pd.DataFrame(tavily_logs)

st.dataframe(

    tavily_df,

    use_container_width=True,

    hide_index=True

)