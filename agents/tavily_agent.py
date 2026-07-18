import os

from tavily import TavilyClient

client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


def tavily_search(question):

    response = client.search(

        query=question,

        search_depth="advanced",

        max_results=5

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