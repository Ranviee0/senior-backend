# endpoints.py
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from db import get_session
from models import Land, Landmark, LandmarkType
from fastapi import UploadFile, File
from utils import haversine
import pandas as pd
import io

router = APIRouter()

@router.post("/create-land/")
def create_land(land: Land):
    with get_session() as session:  # ✅ you don't need to import Session here
        session.add(land)
        session.commit()
        session.refresh(land)
        return land
    
@router.post("/create-landmark/")
def create_landmark(landmark: Landmark):
    with get_session() as session:
        session.add(landmark)
        session.commit()
        session.refresh(landmark)
        return landmark

@router.get("/list-lands/")
def read_lands():
    with get_session() as session:
        lands = session.exec(select(Land)).all()
        return lands

@router.get("/list-landmarks/")
def read_landmarks():
    with get_session() as session:
        landmarks = session.exec(select(Landmark)).all()
        return landmarks

@router.post("/bulk-create-landmarks/")
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

    with get_session() as session:
        session.add_all(landmarks)
        session.commit()

    return {"inserted": len(landmarks)}

from fastapi import HTTPException

@router.get("/land/{land_id}/nearest-landmarks/")
def get_nearest_landmarks(land_id: int):
    with get_session() as session:
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
