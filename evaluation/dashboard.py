import os
import sys

import streamlit as st

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------
# Data
# ---------------------------------------

from evaluation.supabase_reader import get_dashboard_data

# ---------------------------------------
# Metrics
# ---------------------------------------

from evaluation.kpi_metrics import calculate_metrics
from evaluation.chart_metrics import prepare_metrics

# ---------------------------------------
# Charts
# ---------------------------------------

from evaluation.charts.trend import plot_query_trend
from evaluation.charts.pipeline import plot_pipeline_distribution
from evaluation.charts.intents import plot_intents
from evaluation.charts.latency import plot_latency

# ---------------------------------------
# Page
# ---------------------------------------

st.set_page_config(
    page_title="IPL AI Evaluation Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 IPL AI Evaluation Dashboard")

# ======================================================
# Load Dashboard Data
# ======================================================

analytics_df = get_dashboard_data()

# ======================================================
# Metrics
# ======================================================

kpis = calculate_metrics(analytics_df)

chart_data = prepare_metrics(analytics_df)

# ======================================================
# KPI CARDS
# ======================================================

row1 = st.columns(3)

with row1[0]:
    st.metric(
        "Total Queries",
        kpis["total_queries"]
    )

with row1[1]:
    st.metric(
        "Average Latency",
        f'{kpis["avg_latency"]} sec'
    )

with row1[2]:
    st.metric(
        "Success Rate",
        f'{kpis["success_rate"]}%'
    )

row2 = st.columns(3)

with row2[0]:
    st.metric(
        "SQL Queries",
        kpis["sql_queries"]
    )

with row2[1]:
    st.metric(
        "FAISS Queries",
        kpis["rag_queries"]
    )

with row2[2]:
    st.metric(
        "Tavily Queries",
        kpis["tavily_queries"]
    )

# ======================================================
# Query Trend
# ======================================================

st.divider()

st.subheader("📈 Query Trend")

st.plotly_chart(
    plot_query_trend(
        chart_data["trend"]
    ),
    use_container_width=True
)

# ======================================================
# Pipeline + Intent
# ======================================================

st.divider()

left, right = st.columns(2)

with left:

    st.subheader("Pipeline Distribution")

    st.plotly_chart(
        plot_pipeline_distribution(
            chart_data["pipeline"]
        ),
        use_container_width=True
    )

with right:

    st.subheader("Intent Distribution")

    st.plotly_chart(
        plot_intents(
            chart_data["intents"]
        ),
        use_container_width=True
    )

# ======================================================
# Latency
# ======================================================

st.divider()

st.subheader("Average Latency")

st.plotly_chart(
    plot_latency(
        chart_data["latency"]
    ),
    use_container_width=True
)

# ======================================================
# Analytics Table
# ======================================================

st.divider()

st.subheader("Query Explorer")

st.dataframe(
    analytics_df,
    use_container_width=True,
    hide_index=True
)