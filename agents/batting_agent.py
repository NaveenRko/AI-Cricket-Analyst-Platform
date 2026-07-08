from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent

from agents.prompts import BATTING_PROMPT

def get_batting_agent(llm):

    db = SQLDatabase.from_uri(
        "duckdb:///database/ipl.duckdb",

        include_tables=[
            "batting_stats",
            "player_match_stats",
            "player_season_stats",
            "phase_batting",
            "player_milestones",
            "players",
            "matches",
            "deliveries"
        ]
    )

    return create_sql_agent(
        llm=llm,
        db=db,
        verbose=True,
        agent_type="tool-calling",
        prefix=BATTING_PROMPT
    )