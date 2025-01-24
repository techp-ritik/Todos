from sqlmodel import create_engine, SQLModel, Session
from app import setting


# Engine for the whole application
connection_string: str = str(setting.DATABASE_URL).replace(
    "postgresql", "postgresql+psycopg")
engine = create_engine(connection_string, connect_args={
                       "sslmode": "disable"}, pool_recycle=300, pool_size=10)

def create_tables():
    """
    Creates all tables defined by SQLModel metadata.
    """
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    Creates a session generator for interacting with the database.
    """
    with Session(engine) as session:
        yield session

