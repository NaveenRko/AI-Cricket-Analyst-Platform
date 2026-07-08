from agents.rag_agent import get_rag_answer


def get_hybrid_answer(
    llm,
    question,
    sql_agent
):

    # -------------------------
    # SQL
    # -------------------------

    try:

        sql_response = sql_agent.invoke(
            {"input": question}
        )

        sql_answer = sql_response["output"]

    except Exception:

        sql_answer = "No SQL statistics available."

    # -------------------------
    # RAG
    # -------------------------

    rag = get_rag_answer(
        llm,
        question
    )

    rag_answer = rag["answer"]

    rag_docs = rag["rag_docs"]

    # -------------------------
    # FINAL PROMPT
    # -------------------------

    prompt = f"""
You are a senior IPL analyst.

Question:
{question}

SQL Statistics:
{sql_answer}

Knowledge:
{rag_answer}

Create ONE final answer.

Rules:

1. SQL statistics are primary.

2. If SQL has useful statistics,
use them first.

3. If SQL has no statistics,
ignore it completely.

4. Use RAG only for:

- player history
- IPL history
- achievements
- context

5. Never remove:

- numbers
- rankings
- player names

6. Never invent statistics.

7. If SQL and RAG disagree,
trust SQL.

8. Explain why the statistics are significant ONLY if supported by the SQL values.

9. Avoid repetition.

10. Do not mention SQL or database.

11. Compare with other players only when SQL contains comparable statistics.

12. Write like an IPL analyst from Cricbuzz or ESPN Cricinfo while remaining factual.

13. If both contain no answer,
say:

Information not available.

Final Answer:
"""

    response = llm.invoke(prompt)

    return {

        "answer": response.content,

        "rag_docs": rag_docs

    }