def rewrite_question(
    llm,
    history,
    question):

    prompt = f"""
    Conversation:

    {history}

    Current Question:

    {question}

    Rewrite the question so it is
    completely self-contained.

    Return only the rewritten question.
    """

    return llm.invoke(
        prompt
    ).content