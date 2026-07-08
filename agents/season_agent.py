from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent

from agents.prompts import SEASON_PROMPT

def get_season_agent(llm):

    db = SQLDatabase.from_uri(
        "duckdb:///database/ipl.duckdb",

        include_tables=[
            "player_season_stats",
            "team_season_stats",
            "matches",
            "player_milestones"
        ]
    )

    return create_sql_agent(
        llm=llm,
        db=db,
        verbose=True,
        agent_type="tool-calling",
        prefix=SEASON_PROMPT
    )