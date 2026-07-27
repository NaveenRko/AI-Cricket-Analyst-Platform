from agents.search_orchestrator import search_orchestrator


def get_rag_hybrid_answer(
    llm,
    question
):

    return search_orchestrator(
        llm,
        question
    )