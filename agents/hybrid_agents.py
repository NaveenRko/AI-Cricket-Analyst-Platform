# from agents.search_orchestrator import search_orchestrator


# def get_hybrid_answer(

#     llm,

#     question,

#     sql_result_function

# ):

#     sql_result = sql_result_function(

#         llm,

#         question

#     )

#     #sql_df = sql_result["result_df"]
#     import streamlit as st

#     sql_df = sql_result["result_df"]
    
#     st.write("sql_result type:", type(sql_result))
#     st.write("sql_df type:", type(sql_df))
#     st.write(sql_df)
#     st.write(sql_result)

#     if sql_df is not None and not sql_df.empty:

#         return {

#             "answer": sql_result["result_text"],

#             "generated_sql": sql_result["generated_sql"],

#             "sql_result": sql_result["result_json"],

#             "sql_error": sql_result["error"],

#             "rag_docs": [],

#             "tavily_sources": [],

#             "search_used": "sql"

#         }

#     # SQL failed

#     return search_orchestrator(

#         llm,

#         question

#     )

from agents.search_orchestrator import search_orchestrator
import streamlit as st
import traceback

def get_hybrid_answer(llm, question, sql_result_function):

    try:

        st.write("===== ENTERED HYBRID AGENT =====")

        st.write("Calling SQL Agent...")

        sql_result = sql_result_function(llm, question)

        st.write("Returned from SQL Agent")

        st.write("sql_result type:", type(sql_result))
        st.write(sql_result)

        sql_df = sql_result.get("result_df")

        st.write("sql_df type:", type(sql_df))
        st.write(sql_df)

        if sql_df is None:
            st.write("DataFrame is None")
        else:
            st.write("DataFrame.empty =", sql_df.empty)
            st.write("Type of empty =", type(sql_df.empty))

        if sql_df is not None and (not sql_df.empty):

            st.write("Returning SQL Result")

            return {
                "answer": sql_result["result_text"],
                "generated_sql": sql_result["generated_sql"],
                "sql_result": sql_result["result_json"],
                "sql_error": sql_result["error"],
                "rag_docs": [],
                "tavily_sources": [],
                "search_used": "sql"
            }

        st.write("SQL Empty -> Going to Search Orchestrator")

        return search_orchestrator(llm, question)

    except Exception:

        st.error(traceback.format_exc())

        raise