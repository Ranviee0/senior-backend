# db.py
from sqlmodel import SQLModel, create_engine, Session  # ✅ this import is required
from contextlib import contextmanager

sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url, echo=True, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@contextmanager
def get_session():
    with Session(engine) as session:
        yield session
