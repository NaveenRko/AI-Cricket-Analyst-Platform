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
    Rewrite the question for clarity only.

    Do NOT:
    - add IPL players
    - add teams
    - add seasons
    - infer a player from a generic name
    - change the user's intent
    - add information not explicitly present
    - sometimes V Kohli will come as V V Kohli but make as V Kohli ONLY
    
    If the question is ambiguous, preserve the ambiguity.

    Return only the rewritten question.
    """

    return llm.invoke(
        prompt
    ).content