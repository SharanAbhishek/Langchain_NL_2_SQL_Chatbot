import os
from langchain.tools import tool
from sqlalchemy import inspect, text
from database import engine   # datbase.py contains the database connection and engine setup
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.mysql.pymysql import PyMySQLSaver


@tool
def list_tables() -> str:

    """
    List all tables in the db
    """

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    return "\n".join(tables)

@tool
def get_table_schema(table_name : str) -> str:
    """
    list the schema of the table mentioned
    """

    inspector = inspect(engine)

    results=[]

    columns = inspector.get_columns(table_name)

    if table_name not in inspector.get_table_names():
        print(f"{table_name} not present")

    
    for column in columns:
        results.append(f"{column['name']} | {column['type']}")

    return "\n".join(results)



@tool
def execute_sql(query: str) -> str:
    """
    Execute a READ-ONLY MySQL SELECT query.

    Only SELECT statements are allowed.
    """

    query_clean = query.strip().lower()

    if not query_clean.startswith("select"):
        return (
            "Error: Only SELECT queries are allowed."
        )

    try:

        with engine.connect() as connection:

            result = connection.execute(
                text(query)
            )

            rows = result.fetchall()

            if not rows:
                return "Query returned no results."

            columns = result.keys()

            output = []

            output.append(
                " | ".join(columns)
            )

            for row in rows:

                output.append(
                    " | ".join(
                        str(value)
                        for value in row
                    )
                )

            return "\n".join(output)

    except Exception as e:

        return f"SQL execution error: {str(e)}"

# -----
# tools
# -----

tools = [list_tables, get_table_schema, execute_sql]

# ----
# System Prompt
# ----

System_Prompt = """
    You are a MySQL database assistant.

Use the available SQL tools to answer questions
about the database.

Follow this process:

1. Discover tables when necessary.
2. Inspect relevant schemas.
3. Generate valid MySQL SELECT queries.
4. Execute the query.
5. Analyze the result.
6. Give a concise answer.

Never invent database values.
Only execute SELECT queries.
Use previous conversation context for follow-up questions
"""

# ----
# Model
# ----
google_api_key = os.getenv('Google_Gemini_API_key')

model = init_chat_model("google_genai:gemini-3.5-flash",
                        temperature=0.5, google_api_key=google_api_key)

# ----
# Agent 
# ----

def create_my_agent(checkpointer):
    agent = create_agent(
        tools=tools,
        model=model,
        system_prompt=System_Prompt,
        checkpointer=checkpointer
    )

    return agent

