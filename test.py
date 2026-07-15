from dotenv import load_dotenv
import os

from langchain_groq import ChatGroq

from agents.batting_agent import get_batting_result


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.3-70b-versatile",
    temperature=0
)

result = get_batting_result(
    llm,
    "Top 5 run scorers in IPL history"
)

print(result["generated_sql"])

print(result["result"])