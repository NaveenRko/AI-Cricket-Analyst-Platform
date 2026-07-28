def get_hybrid_answer(
    llm,
    question,
    sql_result_function
):

    sql_result = sql_result_function(
        llm,
        question
    )

    return sql_result