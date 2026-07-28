from agents.search_orchestrator import search_orchestrator


def get_hybrid_answer(

    llm,

    question,

    sql_result_function

):

    sql_result = sql_result_function(

        llm,

        question

    )

    #sql_df = sql_result["result_df"]
    import streamlit as st

    sql_df = sql_result["result_df"]
    
    st.write("sql_result type:", type(sql_result))
    st.write("sql_df type:", type(sql_df))
    st.write(sql_df)
    st.write(sql_result)

    if sql_df is not None and not sql_df.empty:

        return {

            "answer": sql_result["result_text"],

            "generated_sql": sql_result["generated_sql"],

            "sql_result": sql_result["result_json"],

            "sql_error": sql_result["error"],

            "rag_docs": [],

            "tavily_sources": [],

            "search_used": "sql"

        }

    # SQL failed

    return search_orchestrator(

        llm,

        question

    )