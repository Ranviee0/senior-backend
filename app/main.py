from fastapi import FastAPI
from sqlmodel import Field, Session, Relationship, SQLModel, create_engine, select
from contextlib import asynccontextmanager
from typing import List, Optional

class Land(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    latitude: float
    longitude: float
    land_size: float

    prices: List["LandPriceHistory"] = Relationship(back_populates="land")

class LandPriceHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    land_id: int = Field(foreign_key="land.id")
    year: int
    price_per_sqm: float

    land: Land = Relationship(back_populates="prices")

class Landmark(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    type: str
    name: str
    latitude: float
    longitude: float

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/create-land/")
def create_land(land: Land):
    with Session(engine) as session:
        session.add(land)
        session.commit()
        session.refresh(land)
        return land
    
@app.post("/create-landmark/")
def create_landmark(landmark: Landmark):
    with Session(engine) as session:
        session.add(landmark)
        session.commit()
        session.refresh(landmark)
        return landmark

@app.get("/list-lands/")
def read_lands():
    with Session(engine) as session:
        lands = session.exec(select(Land)).all()
        return lands

@app.get("/list-landmarks/")
def read_landmarks():
    with Session(engine) as session:
        landmarks = session.exec(select(Landmark)).all()
        return landmarks