from agents.rag_agent import get_rag_answer
from agents.tavily_agent import tavily_search


def get_tavily_answer(llm, question):

    rag = get_rag_answer(llm, question)

    # RAG found answer

    if "information not available" not in rag["answer"].lower():

        rag["search_used"] = "rag"

        return rag

    # Otherwise Tavily

    tavily = tavily_search(question)

    prompt = f"""
Question:
{question}

Search Results:
{tavily['context']}

Answer ONLY using the search results.

Never invent facts.

Never mention Tavily.

Never mention web search.
"""

    response = llm.invoke(prompt)

    usage = response.response_metadata["token_usage"]

    return {

        "answer": response.content,

        "generated_sql": None,

        "sql_result": None,

        "sql_error": None,

        "rag_docs": rag["rag_docs"],

        "tavily_sources": tavily["sources"],

        "search_used": "tavily",

        "usage": usage

    }