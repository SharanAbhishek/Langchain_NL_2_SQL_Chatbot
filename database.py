import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

user = os.getenv('db_user')
password= os.getenv('db_password')
host=os.getenv('db_host')
port=os.getenv('db_port')
info_db=os.getenv('info_db')


DB_URL = (
    f"mysql+pymysql://"
    f"{user}:{password}@{host}:{port}/{info_db}"
)

engine = create_engine(
    DB_URL,
    pool_pre_ping=True
)
