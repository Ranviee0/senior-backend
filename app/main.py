from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
from enum import Enum
from sqlmodel import Field, Session, Relationship, SQLModel, create_engine, select
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from math import radians, cos, sin, asin, sqrt
import io

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance in kilometers between two points on Earth."""
    R = 6371  # Earth radius in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

class LandmarkType(str, Enum):
    MRT = "MRT"
    BTS = "BTS"

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

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

@app.post("/bulk-create-landmarks/")
async def bulk_create_landmarks(file: UploadFile = File(...)):
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

    required_columns = {"type", "name", "latitude", "longitude"}
    if not required_columns.issubset(df.columns):
        raise HTTPException(status_code=400, detail=f"CSV must contain columns: {required_columns}")

    landmarks = [
        Landmark(
            type=row["type"],
            name=row["name"],
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
        )
        for _, row in df.iterrows()
    ]

    with Session(engine) as session:
        session.add_all(landmarks)
        session.commit()

    return {"inserted": len(landmarks)}

from fastapi import HTTPException

@app.get("/land/{land_id}/nearest-landmarks/")
def get_nearest_landmarks(land_id: int):
    with Session(engine) as session:
        land = session.get(Land, land_id)
        if not land:
            raise HTTPException(status_code=404, detail="Land not found")

        result = {}

        for landmark_type in LandmarkType:
            landmarks = session.exec(
                select(Landmark).where(Landmark.type == landmark_type.value)
            ).all()

            if not landmarks:
                result[landmark_type.value] = None  # or "Not found"
                continue

            # Find nearest
            nearest = min(
                landmarks,
                key=lambda lm: haversine(land.latitude, land.longitude, lm.latitude, lm.longitude)
            )
            distance = haversine(land.latitude, land.longitude, nearest.latitude, nearest.longitude)
            result[landmark_type.value] = round(distance, 3)  # Rounded for readability

        return result
