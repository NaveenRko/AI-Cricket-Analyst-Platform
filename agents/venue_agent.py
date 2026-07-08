from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent

from agents.prompts import VENUE_PROMPT

def get_venue_agent(llm):

    db = SQLDatabase.from_uri(
        "duckdb:///database/ipl.duckdb",

        include_tables=[
            "venue_stats",
            "matches"
        ]
    )

    return create_sql_agent(
        llm=llm,
        db=db,
        verbose=True,
        agent_type="tool-calling",
        prefix=VENUE_PROMPT
    )