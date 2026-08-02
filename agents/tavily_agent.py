import os

from tavily import TavilyClient

client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


def tavily_search(question):

    search_query = f"""
You are searching for information about the Indian Premier League (IPL).

User question:
{question}

Interpret all player, team, season, match and performance references
in the context of the IPL unless the question explicitly specifies
another cricket competition.

Return information relevant to IPL cricket only.
"""

    response = client.search(

        query=search_query,

        search_depth="advanced",

        max_results=3

    )

    context = []

    sources = []

    for result in response["results"]:

        context.append(result["content"])

        sources.append(result["url"])

    return {

        "context": "\n\n".join(context),

        "sources": sources

    }