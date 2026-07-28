import duckdb

from langchain_core.prompts import PromptTemplate

DATABASE = "database/ipl.duckdb"

SQL_PROMPT = """
{schema}

User Question:
{question}

SQL:
"""


def generate_and_execute_sql(
    llm,
    question,
    schema
):

    prompt = PromptTemplate(
        template=SQL_PROMPT,
        input_variables=[
            "schema",
            "question"
        ]
    )

    chain = prompt | llm
    
    print("STEP 1")
    response = chain.invoke(
        {
            "schema": schema,
            "question": question
        }
    )
    print("STEP 2")
    sql = response.content.strip()

    sql = sql.replace("```sql", "")
    sql = sql.replace("```", "")
    sql = sql.strip()

    # -------------------------------
    # Safety Check
    # -------------------------------

    if not sql.lower().startswith("select"):

        return {

            "generated_sql": sql,

            "result_df": None,

            "result_json": [],

            "result_text": "Model generated a non-SELECT query.",

            "error": "Model generated a non-SELECT query."

        }

    try:
        print("STEP 3")
        conn = duckdb.connect(DATABASE)
        print("STEP 4")
        df = conn.execute(sql).fetchdf()
        print("STEP 5")
        conn.close()
        print("STEP 6")

        print(type(df))
        print(df.empty)

        return {

            "generated_sql": sql,

            "result_df": df,

            "result_json": df.to_dict(orient="records"),

            "result_text": df.to_markdown(index=False) if not df.empty else "No statistics available.",

            "error": None

        }

    except Exception as e:

        return {

            "generated_sql": sql,

            "result_df": None,

            "result_json": [],

            "result_text": "No statistics available.",

            "error": str(e)

        }