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


import math
import numpy as np


def clean(value):

    if value is None:
        return None

    if isinstance(value, (float, np.floating)):

        if math.isnan(value):
            return None

        return float(value)

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.bool_):
        return bool(value)

    return value

    
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

        "query_log_id": clean(query_log_id),

        "pipeline": clean(pipeline),
    
        "status": clean(status),
    
        "sql_used": clean(sql_used),
    
        "rag_used": clean(rag_used),
    
        "tavily_used": clean(tavily_used),
    
        "generated_sql": clean(generated_sql),
    
        "llm_calls": clean(llm_calls),
    
        "response_time": clean(response_time),
    
        "intent": clean(intent),
    
        "confidence": clean(confidence)

    }).execute()

def save_feedback_log(data):

    response = (
        supabase
        .table("feedback_logs")
        .insert(data)
        .execute()
    )

    return response