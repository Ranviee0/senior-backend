from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.db import get_session
from app.models import Landmark, LandmarkType  # Assuming LandmarkType is an Enum
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from app.utils import haversine
from pathlib import Path
import pandas as pd
import csv
import os
import pickle
import json

router = APIRouter()

@router.post("/generate-and-train/")
def generate_and_train():
    root_dir = Path(__file__).resolve().parents[1]
    landmarks_path = root_dir / "data" / "landmarks.csv"
    land_path = root_dir / "data" / "land.csv"
    finance_path = root_dir / "data" / "land-finance.csv"
    normalized_path = root_dir / "normalized.csv"
    model_path = root_dir / "model.pkl"
    feature_path = root_dir / "features.json"

    if not (landmarks_path.exists() and land_path.exists() and finance_path.exists()):
        raise HTTPException(status_code=400, detail="One or more input files are missing.")

    with get_session() as session:
        # ✅ Load and insert landmarks
        df_landmarks = pd.read_csv(landmarks_path)
        for _, row in df_landmarks.iterrows():
            landmark = Landmark(
                type=row["type"],
                name=row["name"],
                latitude=row["latitude"],
                longitude=row["longitude"]
            )
            session.add(landmark)
        session.commit()

        # ✅ Load land + finance data
        df_land = pd.read_csv(land_path)
        df_land["id"] = df_land.index + 1
        df_finance = pd.read_csv(finance_path)
        df_merged = df_finance.merge(df_land, left_on="land_id", right_on="id")

        # ✅ Compute distances
        dist_maps = []
        landmarks = session.exec(select(Landmark)).all()

        for _, land_row in df_land.iterrows():
            lat, lon = land_row["latitude"], land_row["longitude"]
            dist_map = {}
            for ltype in df_landmarks["type"].unique():
                same_type = [lm for lm in landmarks if lm.type == ltype]
                if not same_type:
                    dist_map[f"dist_{ltype.lower()}"] = 0
                    continue
                nearest = min(same_type, key=lambda lm: haversine(lat, lon, lm.latitude, lm.longitude))
                dist = haversine(lat, lon, nearest.latitude, nearest.longitude)
                dist_map[f"dist_{ltype.lower()}"] = round(dist, 4)
            dist_maps.append(dist_map)

        df_dist = pd.DataFrame(dist_maps)
        df_final = pd.concat([df_merged, df_dist], axis=1)

        # ✅ Save normalized CSV
        df_final.to_csv(normalized_path, index=False)

    # ✅ Train model
    df = pd.read_csv(normalized_path)

    if "land_price" not in df.columns:
        raise HTTPException(status_code=400, detail="Missing 'land_price' column in normalized data.")

    # Infer feature columns dynamically
    distance_cols = [col for col in df.columns if col.startswith("dist_")]
    macro_cols = ["year", "inflation", "interest_rate"]
    basic_cols = ["land_size", "latitude", "longitude"]
    features = basic_cols + distance_cols + macro_cols

    # Validate presence
    if not all(col in df.columns for col in features + ["land_price"]):
        raise HTTPException(status_code=400, detail="Missing one or more required columns.")

    # ✅ Train
    X = df[features]
    y = df["land_price"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # ✅ Save model
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    # ✅ Save feature names
    with open(feature_path, "w") as f:
        json.dump(features, f)

    return {
        "status": "success",
        "message": "Landmarks inserted, data normalized, and model trained.",
        "model_file": model_path.name,
        "features_file": feature_path.name,
    }