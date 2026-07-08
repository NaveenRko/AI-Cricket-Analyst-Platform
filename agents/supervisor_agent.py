from langchain_core.prompts import PromptTemplate

PROMPT = """
You are an IPL supervisor.

Agents:

batting
bowling
venue
matchup
team
season
rag
out_of_scope


Question:
{question}

Return ONLY agent name.
"""

def decide_agent(llm, question):

    prompt = PromptTemplate(
        template=PROMPT,
        input_variables=["question"]
    )

    chain = prompt | llm

    result = chain.invoke(
        {"question": question}
    )

    return result.content.strip().lower()