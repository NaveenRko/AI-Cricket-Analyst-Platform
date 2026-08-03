import json

from langchain_core.prompts import PromptTemplate

SQL_INTENT_ROUTER_PROMPT = """
You are an IPL SQL intent router.

Choose exactly ONE agent for the question.


Agents:

batting = player batting/career statistics:
runs, average, strike rate, fours, sixes, fifties, hundreds,
batting records, highest scores.

bowling = player bowling/career statistics:
wickets, economy, bowling average, bowling strike rate,
runs conceded, bowling records.

team = all-time/historical franchise statistics:
IPL titles, career wins/losses, franchise records.
Do NOT use team when a specific season is being asked.

season = season-specific IPL statistics:
points, position, wins/losses in a season, net run rate,
points table, Orange Cap, Purple Cap, champion, runner-up,
season records, top performers in a specific season.

venue = venue/ground-specific statistics:
highest/lowest score, venue records, ground performance.

matchup = direct comparison:
player vs player, batter vs bowler, team vs team,
head-to-head, dismissals between players.

==================================================
PRIORITY RULES
==================================================

1. Explicit comparison/head-to-head → matchup
2. Venue/ground is the subject → venue
3. Specific season + season/team performance → season
4. Player batting statistic → batting
5. Player bowling statistic → bowling
6. Historical/all-time franchise statistic → team

IMPORTANT:

A team name alone does NOT mean team.

"SRH NRR in IPL 2024" → season
"SRH points in IPL 2024" → season
"SRH wins in IPL 2024" → season

"Kohli runs in IPL 2024" → batting
"Bumrah wickets in IPL 2024" → bowling

"Most IPL runs" → batting
"Most IPL wickets" → bowling
"Most IPL titles" → team

---------------------------------------

Return ONLY JSON.

Examples
{{
    "intent":"batting"
}}

{{
    "intent":"bowling"
}}

{{
    "intent":"team"
}}

{{
    "intent":"venue"
}}

{{
    "intent":"season"
}}

{{
    "intent":"matchup"
}}

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