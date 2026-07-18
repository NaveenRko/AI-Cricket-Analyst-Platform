from agents.rag_agent import get_rag_answer
from agents.tavily_agent import tavily_search

CURRENT_INFO_KEYWORDS = {
    "latest","today","currently","current","retired",
    "retirement","injury","injured","news","recent",
    "now","auction","transfer","released","retained",
    "captain","coach","announcement","ranking","rankings"
}


def needs_live_search(question):

    q = question.lower()

    return any(
        k in q
        for k in CURRENT_INFO_KEYWORDS
    )


def get_rag_hybrid_answer(
    llm,
    question
):

    # ------------------------
    # Current information?
    # ------------------------

    if needs_live_search(question):

        tavily = tavily_search(question)

        prompt = f"""
Question:
{question}

Search Results:
{tavily["context"]}

Answer naturally.
"""

        response = llm.invoke(prompt)

        return {

            "answer": response.content,

            "generated_sql": None,

            "sql_result": None,

            "sql_error": None,

            "rag_docs": [],

            "tavily_sources": tavily["sources"],

            "search_used": "tavily"

        }

    # ------------------------
    # FAISS
    # ------------------------

    rag = get_rag_answer(
        llm,
        question
    )

    if "information not available" not in rag["answer"].lower():

        return {

            "answer": rag["answer"],

            "generated_sql": None,

            "sql_result": None,

            "sql_error": None,

            "rag_docs": rag["rag_docs"],

            "tavily_sources": [],

            "search_used": "rag"

        }

    # ------------------------
    # FAISS Failed
    # ------------------------

    tavily = tavily_search(question)

    prompt = f"""
Question:
{question}

Search Results:
{tavily["context"]}

Answer naturally.
"""

    response = llm.invoke(prompt)

    return {

        "answer": response.content,

        "generated_sql": None,

        "sql_result": None,

        "sql_error": None,

        "rag_docs": rag["rag_docs"],

        "tavily_sources": tavily["sources"],

        "search_used": "tavily"

    }