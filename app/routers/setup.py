from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.db import get_session
from app.models import Landmark, LandmarkType, LandFinanceTrain, LandTrain
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from app.utils import haversine
import pandas as pd
import csv
import os
from pathlib import Path
import pickle


UPLOAD_DIR = "test-post"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()

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


def build_finance_rows(land, finance_records, dist_map):
    rows = []
    for finance in finance_records:
        rows.append({
            "land_size": land.land_size,
            "dist_transit": land.dist_transit,
            "latitude": land.latitude,
            "longitude": land.longitude,
            "dist_cbd": dist_map.get("CBD", 0),
            "dist_bts": dist_map.get("BTS", 0),
            "dist_mrt": dist_map.get("MRT", 0),
            "dist_office": dist_map.get("Office", 0),
            "dist_condo": dist_map.get("Condo", 0),
            "dist_tourist": dist_map.get("Tourist", 0),
            "year": finance.year,
            "land_price": finance.land_price,
            "inflation": finance.inflation,
            "interest_rate": finance.interest_rate,
        })
    return rows


@router.post("/generate-normalized/")
def generate_normalized_land_csv():
    with get_session() as session:
        lands = session.exec(select(LandTrain)).all()
        result_rows = []

        for land in lands:
            finance_records = session.exec(
                select(LandFinanceTrain)
                .where(LandFinanceTrain.land_id == land.id)
                .order_by(LandFinanceTrain.year)
            ).all()

            if not finance_records:
                continue

            dist_map = compute_distance_map(session, land)
            result_rows.extend(build_finance_rows(land, finance_records, dist_map))

        if not result_rows:
            raise HTTPException(status_code=404, detail="No data found to normalize.")

        output_path = Path(__file__).resolve().parents[1] / "normalized.csv"
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=result_rows[0].keys())
            writer.writeheader()
            writer.writerows(result_rows)

        return {"status": "success", "file_path": str(output_path.name)}


@router.post("/train-model/")
def train_land_price_model():
    try:
        root_dir = Path(__file__).resolve().parents[1]
        normalized_path = root_dir / "normalized.csv"
        model_path = root_dir / "model.pkl"

        # Load normalized CSV
        df = pd.read_csv(normalized_path)

        feature_cols = [
            "land_size", "dist_transit", "latitude", "longitude",
            "dist_cbd", "dist_bts", "dist_mrt", "dist_office",
            "dist_condo", "dist_tourist", "year", "inflation", "interest_rate"
        ]

        if not all(col in df.columns for col in feature_cols + ["land_price"]):
            return {"error": "Missing one or more required columns in CSV."}

        # Train model
        X = df[feature_cols]
        y = df["land_price"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Save model
        with open(model_path, "wb") as f:
            pickle.dump(model, f)

        return {
            "status": "success",
            "message": "Model trained and saved successfully.",
            "model_file": str(model_path.name)
        }

    except FileNotFoundError:
        return {"error": "normalized.csv not found. Please run CSV generation first."}
    except Exception as e:
        return {"error": str(e)}