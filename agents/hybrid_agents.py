from agents.rag_agent import get_rag_answer
from agents.tavily_agent import tavily_search


def get_hybrid_answer(
    llm,
    question,
    sql_result_function
):

    # ----------------------------------------
    # SQL
    # ----------------------------------------

    sql_result = sql_result_function(
        llm,
        question
    )

    sql_df = sql_result["result_df"]

    sql_answer = sql_result["result_text"]

    generated_sql = sql_result["generated_sql"]

    sql_json = sql_result["result_json"]

    # ----------------------------------------
    # SQL Found
    # ----------------------------------------

    if sql_df is not None and not sql_df.empty:

        return {

            "answer": sql_answer,

            "generated_sql": generated_sql,

            "sql_result": sql_json,

            "sql_error": sql_result["error"],

            "rag_docs": [],

            "tavily_sources": [],

            "search_used": "sql"

        }

    # ----------------------------------------
    # FAISS RAG
    # ----------------------------------------

    rag = get_rag_answer(
        llm,
        question
    )

    rag_answer = rag["answer"]

    rag_docs = rag["rag_docs"]

    # ----------------------------------------
    # FAISS has useful answer
    # ----------------------------------------

    if (
        rag_answer
        and
        "information not available" not in rag_answer.lower()
    ):

        return {

            "answer": rag_answer,

            "generated_sql": generated_sql,

            "sql_result": sql_json,

            "sql_error": sql_result["error"],

            "rag_docs": rag_docs,

            "tavily_sources": [],

            "search_used": "rag"

        }

    # ----------------------------------------
    # Tavily Search
    # ----------------------------------------

    tavily = tavily_search(question)

    prompt = f"""
You are a senior IPL analyst.

Question:
{question}

Web Search Results:

{tavily["context"]}

Rules

1. Use only the web search results.

2. Never invent facts.

3. Write naturally.

4. Never mention Tavily.

5. Never mention web search.

6. If information is unavailable say:

Information not available.

Answer:
"""

    response = llm.invoke(prompt)

    return {

        "answer": response.content,

        "generated_sql": generated_sql,

        "sql_result": sql_json,

        "sql_error": sql_result["error"],

        "rag_docs": rag_docs,

        "tavily_sources": tavily["sources"],

        "search_used": "tavily"

    }