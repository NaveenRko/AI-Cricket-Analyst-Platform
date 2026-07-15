from agents.rag_agent import get_rag_answer


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
    # Decide whether RAG is needed
    # ----------------------------------------

    use_rag = False

    if sql_df is None:

        use_rag = True

    elif sql_df.empty:

        use_rag = True

    rag_answer = ""

    rag_docs = []

    # ----------------------------------------
    # RAG
    # ----------------------------------------

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

            "generated_sql": generated_sql,

            "sql_result": sql_json,

            "rag_docs": []

        }

    # ----------------------------------------
    # Hybrid Answer
    # ----------------------------------------

    prompt = f"""
You are a senior IPL analyst.

Question:
{question}

SQL Statistics:
{sql_answer}

Knowledge Base:
{rag_answer}

Rules:

1. SQL is the primary source.

2. Use RAG only when SQL contains no statistics.

3. Never invent statistics.

4. Never mention SQL or databases.

5. Never mention RAG or knowledge base.

6. Keep the answer concise and natural.

7. If both SQL and RAG contain no information, reply:

Information not available.

Final Answer:
"""

    response = llm.invoke(prompt)

    return {

        "answer": response.content,
    
        "generated_sql": generated_sql,
    
        "sql_result": sql_json,
    
        "sql_error": sql_result["error"],
    
        "rag_docs": rag_docs
    
    }