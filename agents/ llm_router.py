from langchain_core.prompts import PromptTemplate


ROUTER_PROMPT = """
You are an IPL query routing agent.

Decide ONLY ONE pipeline.

Return ONLY ONE WORD.

sql
rag
tavily

Rules

Use sql when the answer needs statistics,
aggregations,
player records,
venue records,
season data,
comparisons.

Use rag when the answer needs historical knowledge,
biography,
career,
stories,
rules,
team history.

Use tavily when the question is about

latest news

today

recent

current

auction

injury

retirement

captain announcement

coach announcement

Question

{question}
"""


def llm_route(llm, question):

    prompt = PromptTemplate.from_template(ROUTER_PROMPT)

    chain = prompt | llm

    response = chain.invoke({

        "question": question

    })

    route = response.content.strip().lower()

    usage = response.response_metadata["token_usage"]

    return {

        "route": route,

        "usage": usage

    }