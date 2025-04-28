from fastapi import APIRouter
from pydantic import BaseModel
import pandas as pd
import pickle
from pathlib import Path
from app.db import get_session
from app.models import LandTrain, LandmarkType, Landmark
from sqlmodel import select
from app.utils import create_prediction_object
from types import SimpleNamespace
from fastapi import Query
from typing import List

router = APIRouter()

class LandBody(BaseModel):
    area: float
    latitude: float
    longitude: float

class LandFeatures(BaseModel):
    land_size: float
    latitude: float
    longitude: float
    dist_transit: float
    dist_mrt: float
    dist_bts: float
    dist_cbd: float
    dist_office: float
    dist_condo: float
    dist_tourist: float
    year: int
    inflation: float
    interest_rate: float

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

@router.get("/predict-multi/", response_model=List[int])
def predict_land_prices_multi(
    latitude: float = Query(...),
    longitude: float = Query(...),
    land_size: float = Query(...),
):
    try:
        # Step 1: Load model
        model_path = Path(__file__).resolve().parents[1] / "model.pkl"
        with open(model_path, "rb") as f:
            model = pickle.load(f)

        # Step 2: Fixed macro factors
        inflation = 1.5  # <-- your fixed value
        interest_rate = 3.0  # <-- your fixed value

        # Step 3: Create land object
        land = SimpleNamespace(
            latitude=latitude,
            longitude=longitude,
            land_size=land_size
        )

        # Step 4: Build the base prediction object
        with get_session() as session:
            base_features = create_prediction_object(session, land)

        # Step 5: Predict for years 1-5
        predictions = []
        expected_cols = [
        "land_size", "dist_transit", "latitude", "longitude",
        "dist_cbd", "dist_bts", "dist_mrt", "dist_office",
        "dist_condo", "dist_tourist", "year", "inflation", "interest_rate"
        ]

        for year in range(1, 6):
            features_dict = base_features.model_dump()
            features_dict.update({
                "year": year,
                "inflation": inflation,
                "interest_rate": interest_rate
        })

            input_df = pd.DataFrame([features_dict])
            input_df = input_df[expected_cols]

            predicted_price = model.predict(input_df)[0]

            predictions.append(int(round(predicted_price)))  # 🔥 directly append rounded integer

        # ✅ Return after loop
        return predictions

    except FileNotFoundError:
        return {"error": "model.pkl not found. Train the model first."}
    except Exception as e:
        return {"error": str(e)}