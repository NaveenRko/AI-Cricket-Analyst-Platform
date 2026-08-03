import os

from tavily import TavilyClient

client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


def tavily_search(question):

    search_query = f"IPL cricket: {question}".strip()

    # Tavily maximum query length = 400 characters
    if len(search_query) > 400:
        search_query = question[:390]

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