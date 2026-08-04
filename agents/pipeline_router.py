import json

from langchain_core.prompts import PromptTemplate

PIPELINE_ROUTER_PROMPT = """
You are an IPL Query Router.

Your ONLY job is to decide whether the user's question is:
1. IPL-related and which pipeline should answer it, or
2. unrelated to IPL → out_of_scope.

Return ONLY valid JSON.
==================================================
STEP 1 — IPL SCOPE GATE
==================================================

FIRST decide whether the QUESTION itself is about the
Indian Premier League.

A question is IPL-related when its answer is specifically
about IPL teams, players, matches, seasons, statistics,
records, venues, history, rules, auctions, news, or events.

IMPORTANT:
Do NOT consider a question IPL-related merely because a
person/player name happens to exist in IPL.

The question must have an IPL-specific intent.

Examples:

"What is the meaning of Naveen?"
→ out_of_scope

"What does the name Naveen mean?"
→ out_of_scope

"Who is Naveen-ul-Haq?"
→ rag

"What is Naveen-ul-Haq's IPL career?"
→ sql

"Is Naveen-ul-Haq playing in IPL 2026?"
→ tavily

"Who is the best IPL player named Naveen?"
→ sql/rag depending on required information

"Who is Virat Kohli?"
→ rag

"Why is MS Dhoni famous in IPL?"
→ rag

"Latest news about Virat Kohli in IPL"
→ tavily

--------------------------------------
STEP 2 - Pipelines
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

Use for questions unrelated to IPL.

Examples:
name meanings, recipes, coding, mathematics,
weather, general knowledge, unrelated sports,
food ball players, FIFA cup, any other games other than IPL(criket)
non-IPL personal questions.

==================================================
IMPORTANT RULE
==================================================

Never route a question to rag or tavily simply because
the answer exists on the internet.

First ask:

"Is the user's actual question about IPL?"

If NO:
→ out_of_scope

If YES:
→ choose sql, rag, or tavily.
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