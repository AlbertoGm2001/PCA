import os
from dotenv import load_dotenv
from sqlmodel import create_engine, Session, SQLModel
from loguru import logger

load_dotenv()

DATABASE_HOST=os.getenv("DATABASE_HOST")
DATABASE_PORT=os.getenv("DATABASE_PORT")
DATABASE_USER=os.getenv("DATABASE_USER")
DATABASE_PASSWORD=os.getenv("DATABASE_PASSWORD")
DATABASE_NAME=os.getenv("DATABASE_NAME")

# Fallback URI if individual variables are missing
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}" 

engine = create_engine(DATABASE_URL)



def init_db(): 
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session


if __name__ == "__main__":
    init_db()