import os
import uuid
import streamlit as st

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from langgraph.checkpoint.mysql.pymysql import PyMySQLSaver

from agent import create_my_agent


# ============================================================
# Configuration
# ============================================================

load_dotenv()

Chat_Memory_URI = (
    f"mysql+pymysql://"
    f"{os.getenv('db_user')}:"
    f"{os.getenv('db_password')}@"
    f"{os.getenv('db_host')}:"
    f"{os.getenv('db_port')}/"
    f"{os.getenv('chat_memory_db')}"
)

chat_db_engine = create_engine(Chat_Memory_URI)


# ============================================================
# Session state
# ============================================================

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:

    st.title("Chat History")

    # New Chat
    if st.button(
        "＋ New Chat",
        use_container_width=True
    ):
        st.session_state.thread_id = None
        st.rerun()

    st.divider()

    # Get persistent chat IDs
    with chat_db_engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT thread_id
                FROM chat_sessions
                ORDER BY updated_at DESC
            """)
        )

        chat_ids = [row[0] for row in result]

    # Display chat IDs
    for chat_id in chat_ids:

        if st.button(
            chat_id,
            key=f"chat_{chat_id}",
            use_container_width=True
        ):

            st.session_state.thread_id = chat_id
            st.rerun()


# ============================================================
# Main UI
# ============================================================

st.title("MySQL Data Assistant")


# ============================================================
# MySQL checkpointer
# ============================================================

with PyMySQLSaver.from_conn_string(
    Chat_Memory_URI
) as checkpointer:

    checkpointer.setup()

    agent = create_my_agent(checkpointer)

    # --------------------------------------------------------
    # Load selected chat
    # --------------------------------------------------------

    if st.session_state.thread_id:

        config = {
            "configurable": {
                "thread_id": st.session_state.thread_id
            }
        }

        checkpoint = checkpointer.get(config)

        if checkpoint:

            messages = (
                checkpoint
                .get("channel_values", {})
                .get("messages", [])
            )

            for message in messages:

                message_type = getattr(
                    message,
                    "type",
                    ""
                )

                if message_type == "human":

                    with st.chat_message("user"):
                        st.write(message.content)

                elif message_type == "ai":

                    if message.content:

                        with st.chat_message("assistant"):
                            st.write(message.content)

    # --------------------------------------------------------
    # Chat input
    # --------------------------------------------------------

    user_input = st.chat_input(
        "Ask a question about your data..."
    )

    if user_input:

        # Create thread ONLY when user sends first message
        if st.session_state.thread_id is None:

            st.session_state.thread_id = str(uuid.uuid4())

            with chat_db_engine.begin() as connection:

                connection.execute(
                    text("""
                        INSERT INTO chat_sessions
                            (thread_id, title)
                        VALUES
                            (:thread_id, :title)
                    """),
                    {
                        "thread_id": st.session_state.thread_id,
                        "title": user_input[:50]
                    }
                )

        config = {
            "configurable": {
                "thread_id": st.session_state.thread_id
            }
        }

        # Display user message
        with st.chat_message("user"):
            st.write(user_input)

        # Invoke agent
        response = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
            },
            config=config
        )

        # Get final answer
        assistant_message = response["messages"][-1].content

        if isinstance(assistant_message, list):
            assistant_message = "\n".join(
            item["text"]
            for item in assistant_message
            if item.get("type") == "text"
)

        with st.chat_message("assistant"):
            st.write(assistant_message)

        # Update timestamp
        with chat_db_engine.begin() as connection:

            connection.execute(
                text("""
                    UPDATE chat_sessions
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE thread_id = :thread_id
                """),
                {
                    "thread_id": st.session_state.thread_id
                }
            )