
from agents.sql_generator import generate_and_execute_sql

from agents.schemas.batting_schema import BATTING_SQL_SCHEMA


def get_batting_result(
    llm,
    question
):

    return generate_and_execute_sql(

        llm=llm,

        question=question,

        schema=BATTING_SQL_SCHEMA

    )



