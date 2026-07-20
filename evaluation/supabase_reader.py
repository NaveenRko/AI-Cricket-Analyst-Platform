import os
import sys
import pandas as pd

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)

from database.supabase_client import supabase


def _to_dataframe(response):

    """
    Converts Supabase response into a clean DataFrame.
    Always returns a DataFrame.
    """

    if response is None:
        return pd.DataFrame()

    data = response.data

    if data is None:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    if df.empty:
        return df

    # Convert timestamp if present
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            utc=True,
            errors="coerce"
        )

    return df


def get_query_logs():

    response = (
        supabase
        .table("query_logs")
        .select("*")
        .order("timestamp", desc=True)
        .execute()
    )

    return _to_dataframe(response)


def get_sql_logs():

    response = (
        supabase
        .table("sql_logs")
        .select("*")
        .execute()
    )

    return _to_dataframe(response)


def get_tavily_logs():

    response = (
        supabase
        .table("tavily_logs")
        .select("*")
        .execute()
    )

    return _to_dataframe(response)


def get_evaluation_logs():

    response = (
        supabase
        .table("evaluation_logs")
        .select("*")
        .execute()
    )

    return _to_dataframe(response)

def get_dashboard_data():

    query_logs = get_query_logs()

    evaluation_logs = get_evaluation_logs()

    sql_logs = get_sql_logs()

    tavily_logs = get_tavily_logs()

    # -----------------------------
    # Query + Evaluation
    # -----------------------------

    df = query_logs.merge(

        evaluation_logs,

        left_on="id",

        right_on="query_log_id",

        how="left",

        suffixes=("", "_eval")

    )

    # -----------------------------
    # SQL Logs
    # -----------------------------

    df = df.merge(

        sql_logs,

        left_on="id",

        right_on="query_log_id",

        how="left",

        suffixes=("", "_sql")

    )

    # -----------------------------
    # Tavily Logs
    # -----------------------------

    df = df.merge(

        tavily_logs,

        left_on="id",

        right_on="query_log_id",

        how="left",

        suffixes=("", "_tavily")

    )

    return df

def get_feedback_logs():

    response = (
        supabase
        .table("feedback_logs")
        .select("*")
        .execute()
    )

    return _to_dataframe(response)

feedback_logs = get_feedback_logs()

df = df.merge(

    feedback_logs,

    left_on="id",

    right_on="query_log_id",

    how="left",

    suffixes=("", "_feedback")

)