from fastapi import APIRouter
from pydantic import BaseModel
import pandas as pd
import pickle
from pathlib import Path
from app.db import get_session
from app.models import Landmark, LandmarkType, LandTrain
from app.utils import haversine
from sqlmodel import select

router = APIRouter()

class LandBody(BaseModel):
    area: float
    lattitude: float
    longitude: float

class LandFeatures(BaseModel):
    land_size: float
    dist_transit: float
    latitude: float
    longitude: float
    dist_cbd: float
    dist_bts: float
    dis_mrt: float
    dist_office: float
    dist_condo: float
    dist_tourist: float
    year: int
    inflation: float
    interest_rate: float

def generate_dist(lattitude, longitude):
    return {
        lattitude: lattitude,
        longitude: longitude
    }

def compute_distance_map(session, land):
    dist_map = {}
    for landmark_type in LandmarkType:
        landmarks = session.exec(
            select(Landmark).where(Landmark.type == landmark_type.value)
        ).all()
        if not landmarks:
            dist_map[landmark_type.value] = 0.0
            continue

        nearest = min(
            landmarks,
            key=lambda lm: haversine(
                land.latitude, land.longitude, lm.latitude, lm.longitude
            ),
        )
        dist = haversine(
            land.latitude, land.longitude, nearest.latitude, nearest.longitude
        )
        dist_map[landmark_type.value] = round(dist, 4)

    return dist_map

@router.post("/")
def predict_land_price(features: LandFeatures):
    try:
        # Load model
        model_path = Path(__file__).resolve().parents[1] / "model.pkl"
        with open(model_path, "rb") as f:
            model = pickle.load(f)

        # Convert input to DataFrame
        input_df = pd.DataFrame([features.model_dump()])

        # Predict
        prediction = model.predict(input_df)[0]

        return {"predicted_land_price": prediction}

    except FileNotFoundError:
        return {"error": "model.pkl not found. Train the model first."}
    except Exception as e:
        return {"error": str(e)}


@router.get("/dist_maps/")
def read_land_trains():
    with get_session() as session:
        lands = session.exec(select(LandTrain)).all()

        dist_maps = []  # create an empty list to collect results
        for land in lands:
            dist_map = compute_distance_map(session, land)
            dist_maps.append(dist_map)  # append each dist_map into the list
        
        return dist_maps  # return the full list after the loop
