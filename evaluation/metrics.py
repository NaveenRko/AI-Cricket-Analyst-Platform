import pandas as pd

def calculate_metrics(query_logs):

    df = pd.DataFrame(query_logs)

    if df.empty:

        return {

            "total_queries": 0,

            "sql_queries": 0,

            "rag_queries": 0,

            "tavily_queries": 0,

            "avg_latency": 0,

            "success_rate": 0

        }

    total_queries = len(df)

    avg_latency = round(df["response_time"].mean(),2)

    success_rate = round(((df["status"] == "success").sum()/ total_queries) * 100,2)

    sql_queries = ((df["pipeline"] == "sql").sum())

    rag_queries = ((df["pipeline"] == "rag").sum())

    tavily_queries = ((df["pipeline"] == "tavily").sum())

    return {

        "total_queries": total_queries,

        "sql_queries": sql_queries,

        "rag_queries": rag_queries,

        "tavily_queries": tavily_queries,

        "avg_latency": avg_latency,

        "success_rate": success_rate

    }