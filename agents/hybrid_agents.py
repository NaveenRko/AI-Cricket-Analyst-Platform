from agents.rag_agent import get_rag_answer
from agents.tavily_agent import tavily_search


CURRENT_INFO_KEYWORDS = {

    "latest",
    "today",
    "currently",
    "current",
    "retired",
    "retirement",
    "injury",
    "injured",
    "news",
    "recent",
    "now",
    "auction",
    "transfer",
    "released",
    "retained",
    "captain",
    "coach",
    "announcement",
    "ranking",
    "rankings"

}


def needs_live_search(question: str):

    q = question.lower()

    return any(

        keyword in q

        for keyword in CURRENT_INFO_KEYWORDS

    )


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

    generated_sql = sql_result["generated_sql"]

    sql_json = sql_result["result_json"]

    sql_error = sql_result["error"]

    sql_answer = sql_result["result_text"]

    # ----------------------------------------
    # SQL Success
    # ----------------------------------------

    if sql_df is not None and not sql_df.empty:

        return {

            "answer": sql_answer,

            "generated_sql": generated_sql,

            "sql_result": sql_json,

            "sql_error": sql_error,

            "rag_docs": [],

            "tavily_sources": [],

            "search_used": "sql"

        }

    # ----------------------------------------
    # LIVE SEARCH QUESTIONS
    # Skip FAISS
    # ----------------------------------------

    if needs_live_search(question):

        tavily = tavily_search(question)

        prompt = f"""
You are a senior IPL analyst.

Question:
{question}

Web Search Results:
{tavily["context"]}

Rules

1. Answer ONLY using the search results.

2. Never invent facts.

3. Keep the answer concise.

4. Never mention Tavily.

5. Never mention web search.

6. If unavailable say:
Information not available.

Answer:
"""

        response = llm.invoke(prompt)

        return {

            "answer": response.content,

            "generated_sql": generated_sql,

            "sql_result": sql_json,

            "sql_error": sql_error,

            "rag_docs": [],

            "tavily_sources": tavily["sources"],

            "search_used": "tavily"

        }

    # ----------------------------------------
    # FAISS
    # ----------------------------------------

    rag = get_rag_answer(

        llm,

        question

    )

    rag_answer = rag["answer"]

    rag_docs = rag["rag_docs"]

    if (

        rag_answer

        and

        "information not available" not in rag_answer.lower()

    ):

        return {

            "answer": rag_answer,

            "generated_sql": generated_sql,

            "sql_result": sql_json,

            "sql_error": sql_error,

            "rag_docs": rag_docs,

            "tavily_sources": [],

            "search_used": "rag"

        }

    # ----------------------------------------
    # FAISS Failed → Tavily
    # ----------------------------------------

    tavily = tavily_search(question)

    prompt = f"""
You are a senior IPL analyst.

Question:
{question}

Web Search Results:
{tavily["context"]}

Rules

1. Answer ONLY using the search results.

2. Never invent facts.

3. Never mention Tavily.

4. Never mention web search.

5. If unavailable say:
Information not available.

Answer:
"""

    response = llm.invoke(prompt)

    return {

        "answer": response.content,

        "generated_sql": generated_sql,

        "sql_result": sql_json,

        "sql_error": sql_error,

        "rag_docs": rag_docs,

        "tavily_sources": tavily["sources"],

        "search_used": "tavily"

    }