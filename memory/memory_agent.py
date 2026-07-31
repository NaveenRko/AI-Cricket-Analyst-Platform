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
    if question contains venue or player, consider it is about IPL venue and IPL player

    Return only the rewritten question.
    """

    return llm.invoke(
        prompt
    ).content