from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent

from agents.prompts import BOWLING_PROMPT

def get_bowling_agent(llm):

    db = SQLDatabase.from_uri(
        "duckdb:///database/ipl.duckdb",

        include_tables=[
            "bowling_stats",
            "phase_bowling",
            "bowler_match_stats",
            "bowler_season_stats",
            "matches",
            "deliveries"
        ]
    )

    return create_sql_agent(
        llm=llm,
        db=db,
        verbose=True,
        agent_type="tool-calling",
        prefix=BOWLING_PROMPT
    )