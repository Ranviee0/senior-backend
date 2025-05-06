from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
import pandas as pd
import pickle
from pathlib import Path
from app.db import get_session
from app.utils import create_prediction_object
from types import SimpleNamespace
from fastapi import Query
from typing import List
import json

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

@router.get("/predict-multi/", response_model=List[int])
def predict_land_prices_multi(
    latitude: float = Query(...),
    longitude: float = Query(...),
    land_size: float = Query(...),
):
    try:
        root_dir = Path(__file__).resolve().parents[1]
        model_path = root_dir / "model.pkl"
        feature_path = root_dir / "features.json"

        # ✅ Load model
        with open(model_path, "rb") as f:
            model = pickle.load(f)
            if isinstance(model, tuple):
                model = model[0]  # unpack if tuple

        # ✅ Load expected features
        with open(feature_path, "r") as f:
            expected_cols = json.load(f)

        # ✅ Fixed macroeconomic values
        inflation = 1.5
        interest_rate = 3.0

        # ✅ Land input
        land = SimpleNamespace(latitude=latitude, longitude=longitude, land_size=land_size)

        # ✅ Build features
        with get_session() as session:
            base_features = create_prediction_object(session, land)

        predictions = []

        for year in range(1, 6):
            features_dict = base_features.model_dump()
            features_dict.update({
                "year": year,
                "inflation": inflation,
                "interest_rate": interest_rate
            })

            input_df = pd.DataFrame([features_dict])

            # Ensure the feature order and presence
            missing_cols = [col for col in expected_cols if col not in input_df.columns]
            if missing_cols:
                raise HTTPException(status_code=400, detail=f"Missing input features: {missing_cols}")

            input_df = input_df[expected_cols]

            predicted_price = model.predict(input_df)[0]
            predictions.append(int(round(predicted_price)))

        return predictions

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="model.pkl or features.json not found. Train the model first.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
