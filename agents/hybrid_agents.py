from agents.rag_agent import get_rag_answer


def get_hybrid_answer(
    llm,
    question,
    sql_result_function
):
    """
    sql_result_function:
        get_batting_result
        get_bowling_result
        get_team_result
        get_season_result
        get_venue_result
        get_matchup_result
    """

    # ----------------------------------------
    # SQL
    # ----------------------------------------

    sql_result = sql_result_function(
        llm,
        question
    )

    sql_answer = sql_result["result"]

    # ----------------------------------------
    # Decide if RAG is needed
    # ----------------------------------------

    use_rag = False

    if isinstance(sql_answer, str):

        lower = sql_answer.lower()

        if (
            "no statistics" in lower
            or "not available" in lower
            or "no rows" in lower
        ):
            use_rag = True

    rag_answer = ""

    rag_docs = []

    if use_rag:

        rag = get_rag_answer(
            llm,
            question
        )

        rag_answer = rag["answer"]

        rag_docs = rag["rag_docs"]

    # ----------------------------------------
    # SQL only
    # ----------------------------------------

    if not use_rag:

        return {
            "answer": sql_answer,
            "rag_docs": []
        }

    # ----------------------------------------
    # Hybrid Answer
    # ----------------------------------------

    prompt = f"""
You are a senior IPL analyst.

Question:
{question}

SQL Result:
{sql_answer}

Knowledge:
{rag_answer}

Rules

1. SQL is the primary source.

2. Use RAG only if SQL lacks statistics.

3. Never invent statistics.

4. Never mention SQL.

5. Never mention RAG.

6. Write naturally.

7. If both have no answer,
say:

Information not available.

Final Answer:
"""

    response = llm.invoke(prompt)

    return {

        "answer": response.content,

        "rag_docs": rag_docs

    }