from agents.sql_generator import generate_and_execute_sql

from agents.schemas.team_schema import SCHEMA


def get_team_result(
    llm,
    question
):

    return generate_and_execute_sql(
        llm=llm,
        question=question,
        schema=SCHEMA
    )