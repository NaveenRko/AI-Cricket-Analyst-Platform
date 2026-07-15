from agents.sql_generator import generate_and_execute_sql

from agents.schemas.matchup_schema import SCHEMA


def get_matchup_result(
    llm,
    question
):

    return generate_and_execute_sql(
        llm=llm,
        question=question,
        schema=SCHEMA
    )