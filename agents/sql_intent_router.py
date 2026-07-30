import json

from langchain_core.prompts import PromptTemplate

SQL_INTENT_ROUTER_PROMPT = """
You are an IPL SQL Router.

The question has ALREADY been classified as SQL.

Your ONLY job is to decide which SQL agent should answer it.

Return ONLY JSON.

---------------------------------------
Available SQL Agents
---------------------------------------

batting

Questions about

Runs

Strike rate

Average

Centuries

Fifties

Fours

Sixes

Highest score

Batting records

Powerplay batting

---------------------------------------

bowling

Questions about

Wickets

Economy

Bowling average

Strike rate

Best bowling

Powerplay bowling

Death bowling

---------------------------------------

team

Questions about

Team wins

Team losses

Points

Franchise records

Team batting

Team bowling

---------------------------------------

venue

Questions about

Venue statistics

Highest scores

Lowest scores

Average scores

Venue records

Ground records

---------------------------------------

season

Questions about

Season statistics

Orange Cap

Purple Cap

Season winners

Season records

---------------------------------------

matchup

Questions about

Head to head

Player vs player

Batter vs bowler

Team vs team

---------------------------------------

Return ONLY JSON.

Examples

{
    "intent":"batting"
}

{
    "intent":"bowling"
}

{
    "intent":"team"
}

{
    "intent":"venue"
}

{
    "intent":"season"
}

{
    "intent":"matchup"
}

Question

{question}
"""


def sql_intent_router(

    llm,

    question

):

    prompt = PromptTemplate(

        template=SQL_INTENT_ROUTER_PROMPT,

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

            "intent": "batting"

        }

    route["usage"] = usage

    return route