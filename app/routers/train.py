from fastapi import APIRouter, HTTPException,File, Form, UploadFile
from sqlmodel import select
from app.db import get_session
from app.models import Land, Landmark, LandmarkType, LandFinance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from app.utils import haversine
import pandas as pd
import csv
import os
from pathlib import Path
import pickle
from typing import List, Optional
from datetime import datetime
import json

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
            "dis_mrt": dist_map.get("MRT", 0),
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
        lands = session.exec(select(Land)).all()
        result_rows = []

        for land in lands:
            finance_records = session.exec(
                select(LandFinance)
                .where(LandFinance.land_id == land.id)
                .order_by(LandFinance.year)
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
        prediction_output_path = root_dir / "predicted_next_year.csv"

        # Load normalized CSV
        df = pd.read_csv(normalized_path)

        feature_cols = [
            "land_size", "dist_transit", "latitude", "longitude",
            "dist_cbd", "dist_bts", "dis_mrt", "dist_office",
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
        with open(root_dir / "model.pkl", "wb") as f:
            pickle.dump(model, f)

        # Predict next year for each land
        latest_years_df = df.sort_values("year").groupby(
            ["latitude", "longitude"], as_index=False
        ).last()

        predict_next = latest_years_df.copy()
        predict_next["year"] = predict_next["year"] + 1

        X_next = predict_next[feature_cols]
        predict_next["predicted_land_price_next_year"] = model.predict(X_next)

        # Save predictions
        predict_next.to_csv(prediction_output_path, index=False)

        return {
            "status": "success",
            "message": "Model trained and next year predictions saved.",
            "prediction_file": str(prediction_output_path.name)
        }

    except FileNotFoundError:
        return {"error": "normalized.csv not found. Please run CSV generation first."}
    except Exception as e:
        return {"error": str(e)}

@router.post("/test-model/")
def test_land_price_model():
    try:
        root_dir = Path(__file__).resolve().parents[1]
        model_path = root_dir / "model.pkl"
        csv_path = root_dir / "normalized.csv"

        if not model_path.exists():
            return {"error": "Trained model file not found. Please run /train-model/ first."}
        if not csv_path.exists():
            return {"error": "normalized.csv not found. Please run /generate-normalized/ first."}

        # Load model
        with open(model_path, "rb") as f:
            model = pickle.load(f)

        # Load data
        df = pd.read_csv(csv_path)
        feature_cols = [
            "land_size", "dist_transit", "latitude", "longitude",
            "dist_cbd", "dist_bts", "dis_mrt", "dist_office",
            "dist_condo", "dist_tourist", "year", "inflation", "interest_rate"
        ]

        if not all(col in df.columns for col in feature_cols + ["land_price"]):
            return {"error": "Missing one or more required columns in CSV."}

        X_test = df[feature_cols]
        y_true = df["land_price"]
        y_pred = model.predict(X_test)

        # Metrics
        r2 = r2_score(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)

        return {
            "status": "success",
            "r2_score": round(r2, 4),
            "mean_absolute_error": round(mae, 2),
            "mean_squared_error": round(mse, 2),
        }

    except Exception as e:
        return {"error": str(e)}


@router.post("/upload")
async def upload(
    land_name: str = Form(...),
    description: str = Form(...),
    area: float = Form(...),
    price: float = Form(...),
    address: str = Form(...),
    lattitude: float = Form(...),
    longitude: float = Form(...),
    zoning: Optional[str] = Form(None),
    pop_density: float = Form(...),
    flood_risk: str = Form(...),
    nearby_dev_plan: List[str] = Form(...),
    images: Optional[List[UploadFile]] = File(None)
):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    json_data = {
        "land_name": land_name,
        "description": description,
        "area": area,
        "price": price,
        "address": address,
        "lattitude": lattitude,
        "longitude": longitude,
        "zoning": zoning,
        "pop_density": pop_density,
        "flood_risk": flood_risk,
        "nearby_dev_plan": nearby_dev_plan,
        "uploaded_at": timestamp
    }

    json_path = os.path.join(UPLOAD_DIR, f"{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    if images:
        for i, image in enumerate(images):
            ext = os.path.splitext(image.filename)[-1]
            file_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{i+1}{ext}")
            with open(file_path, "wb") as f:
                f.write(await image.read())

    return {"message": "Upload successful", "timestamp": timestamp}