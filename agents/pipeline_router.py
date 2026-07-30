import json

from langchain_core.prompts import PromptTemplate

PIPELINE_ROUTER_PROMPT = """
You are an IPL Query Router.

Your ONLY job is to decide which pipeline should answer the user's question.

Return ONLY valid JSON.

--------------------------------------
Pipelines
--------------------------------------

1. sql

Use SQL if the answer exists inside IPL structured statistics.

Examples

Highest run scorer
Highest wicket taker
Strike rate
Batting average
Economy
Venue statistics
Season statistics
Team statistics
Head to head
Player comparisons
Match statistics
Orange Cap winners
Purple Cap winners

--------------------------------------

2. rag

Use RAG if the question requires historical knowledge or explanation.

Examples

Who is Virat Kohli?

Explain Orange Cap.

History of IPL.

Who is Shane Warne?

Career of Rohit Sharma.

Why is MS Dhoni famous?

--------------------------------------

3. tavily

Use Tavily ONLY for CURRENT information.

Examples

Latest IPL news

Today's IPL match

Current captain

Injury news

Retired players

Auction updates

Retained players

Released players

Coach announcement

Recent rankings

--------------------------------------

4. out_of_scope

Everything unrelated to IPL.

--------------------------------------

Return ONLY JSON.

Examples

{{
    "pipeline":"sql"
}}

{{
    "pipeline":"rag"
}}

{{
    "pipeline":"tavily"
}}

{{
    "pipeline":"out_of_scope"
}}

Question

{question}
"""


def pipeline_router(
    llm,
    question
):

    prompt = PromptTemplate(

        template=PIPELINE_ROUTER_PROMPT,

        input_variables=["question"]

    )

    chain = prompt | llm

    response = chain.invoke(

        {

            "question": question

        }

    )

    usage = response.response_metadata["token_usage"]

    try:

        content = response.content.strip()

        content = content.replace("```json", "")

        content = content.replace("```", "")

        route = json.loads(content)

    except Exception:

        route = {

            "pipeline": "rag"

        }

    route["usage"] = usage

    return route