import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from database.supabase_client import supabase


# ----------------------------
# Query Logs
# ----------------------------

def get_query_logs():

    response = (
        supabase
        .table("query_logs")
        .select("*")
        .order("timestamp", desc=True)
        .execute()
    )

    return response.data


# ----------------------------
# SQL Logs
# ----------------------------

def get_sql_logs():

    response = (
        supabase
        .table("sql_logs")
        .select("*")
        .execute()
    )

    return response.data


# ----------------------------
# Tavily Logs
# ----------------------------

def get_tavily_logs():

    response = (
        supabase
        .table("tavily_logs")
        .select("*")
        .execute()
    )

    return response.data