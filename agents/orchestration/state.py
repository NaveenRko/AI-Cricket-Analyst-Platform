from typing import TypedDict, Optional


class IPLState(TypedDict, total=False):

    question: str

    rewritten_question: str

    conversation_history: list

    pipeline: str

    intent: str

    sql: Optional[str]

    sql_result: Optional[str]

    rag_context: Optional[str]

    web_context: Optional[str]

    sources: list

    answer: Optional[str]

    error: Optional[str]

    retry_count: int