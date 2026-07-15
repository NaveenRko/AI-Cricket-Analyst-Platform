from database.supabase_client import supabase

def save_query(data):

    response = (
        supabase
        .table("query_logs")
        .insert(data)
        .execute()
    )

    return response.data[0]["id"]

import pandas as pd


def save_sql_log(

    query_log_id,

    generated_sql,

    sql_result,

    error
):

    if isinstance(sql_result, pd.DataFrame):

        sql_result = sql_result.to_dict(
            orient="records"
        )

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