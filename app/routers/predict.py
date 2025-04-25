from fastapi import APIRouter
from pydantic import BaseModel
import pandas as pd
import pickle
from pathlib import Path

router = APIRouter()

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
