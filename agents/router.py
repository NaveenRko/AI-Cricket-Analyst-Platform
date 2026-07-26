from langchain_core.prompts import PromptTemplate
import json

ROUTER_PROMPT = """
You are an IPL AI Router.

Your job is ONLY to decide which pipeline should answer the question.

Available SQL intents

- batting
- bowling
- venue
- season
- team
- matchup

Use pipeline="sql" ONLY if the question can be answered from structured IPL statistics.

Examples:

Top run scorer
Highest strike rate
Best bowling figures
Venue statistics
Season statistics
Head to head
Player comparisons
Team statistics
Match statistics

----------------------------

Use pipeline="rag" when the question requires historical cricket knowledge, biography, achievements or explanations.

Examples

Who is Virat Kohli?
Tell me about Shane Warne.
Explain Orange Cap.
History of IPL.
Why is MS Dhoni famous?
Career of Jasprit Bumrah.

----------------------------

Use pipeline="tavily" when the question requires CURRENT information.

Examples

today
latest
recent
current
auction
injury
injured
captain announcement
coach announcement
retirement
released
retained
news
ranking

----------------------------

Use pipeline="out_of_scope" when the question is unrelated to IPL.

Return ONLY valid JSON.

SQL example

{{
    "pipeline":"sql",
    "intent":"batting"
}}

RAG example

{{
    "pipeline":"rag"
}}

Tavily example

{{
    "pipeline":"tavily"
}}

Out of scope example

{{
    "pipeline":"out_of_scope"
}}

Question

{question}
"""

def llm_router(llm, question):

    prompt = PromptTemplate(
        template=ROUTER_PROMPT,
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

        # Remove markdown if model returns ```json
        content = content.replace("```json", "")
        content = content.replace("```", "")
        
        route = json.loads(content)

    except Exception:

        route = {
            "pipeline": "rag"
        }

    route["usage"] = usage

    return route

