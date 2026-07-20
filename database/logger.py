from database.supabase_client import supabase


def save_query(data):

    response = (
        supabase
        .table("query_logs")
        .insert(data)
        .execute()
    )

    return response.data[0]["id"]


def save_sql_log(

    query_log_id,

    generated_sql,

    sql_result,

    error

):

    # SQL Agent wasn't used
    if generated_sql is None:
        return

    (
        supabase
        .table("sql_logs")
        .insert({

            "query_log_id": query_log_id,

            "generated_sql": generated_sql,

            "sql_result": sql_result,

            "error": error

        })
        .execute()
    )

def save_tavily_log(

    query_log_id,

    search_used,

    tavily_sources

):

    if search_used != "tavily":
        return

    (
        supabase
        .table("tavily_logs")
        .insert({

            "query_log_id": query_log_id,

            "search_used": search_used,

            "tavily_sources": tavily_sources

        })
        .execute()
    )

def save_evaluation_log(

    query_log_id,

    pipeline,

    status,

    sql_used,

    rag_used,

    tavily_used,

    generated_sql,

    llm_calls,

    response_time,

    intent,

    confidence=None

):

    supabase.table("evaluation_logs").insert({

        "query_log_id": query_log_id,

        "pipeline": pipeline,

        "status": status,

        "sql_used": sql_used,

        "rag_used": rag_used,

        "tavily_used": tavily_used,

        "generated_sql": generated_sql,

        "llm_calls": llm_calls,

        "response_time": response_time,

        "intent": intent,

        "confidence": confidence

    }).execute()

def save_feedback_log(data):

    response = (
        supabase
        .table("feedback_logs")
        .insert(data)
        .execute()
    )

    return response