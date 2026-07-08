from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent

from agents.prompts import MATCHUP_PROMPT

def get_matchup_agent(llm):

    db = SQLDatabase.from_uri(
        "duckdb:///database/ipl.duckdb",

        include_tables=[
            "player_vs_player",
            "deliveries",
            "matches"
        ]
    )

    return create_sql_agent(
        llm=llm,
        db=db,
        verbose=True,
        agent_type="tool-calling",
        prefix=MATCHUP_PROMPT
    )