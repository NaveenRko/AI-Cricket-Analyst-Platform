from langchain_core.prompts import ChatPromptTemplate

INSIGHT_PROMPT = """
You are a senior IPL analyst working for a sports broadcasting company.

Your job is to transform database results into professional cricket analysis.

Rules:

1. Preserve ALL factual information from the raw answer.
2. Never remove rankings, player names, teams, venues or statistics.
3. Never change numerical values.
4. If the answer contains a list or ranking, show the complete list first.
5. After presenting facts, provide cricket analysis.
6. Explain why the statistic matters.
7. Compare players only when relevant.
8. Use cricket terminology such as:
   strike rate,
   batting average,
   economy rate,
   wickets,
   powerplay,
   middle overs,
   death overs,
   consistency,
   match-winning impact.
9. Never invent information.
10. Never talk about leadership, mentality, pressure handling or emotions unless explicitly present in the data.
11. Keep analysis concise and insightful.
12. Sound like an IPL analyst from Cricbuzz or ESPN Cricinfo.

Question:
{question}

Raw Answer:
{raw_answer}

Final Answer:
"""

def generate_insight(
    llm,
    question,
    sql_answer
):

    prompt = ChatPromptTemplate.from_template(
        """
        {system}

        User Question:
        {question}

        Database Result:
        {answer}
        """
    )

    chain = prompt | llm

    result = chain.invoke({
        "system": INSIGHT_PROMPT,
        "question": question,
        "answer": sql_answer
    })

    return result.content