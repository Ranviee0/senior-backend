from fastapi import APIRouter, HTTPException, UploadFile, File
from sqlmodel import select
from db import get_session
from models import Land, Landmark, LandmarkType, LandFinance
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from utils import haversine
import pandas as pd
import io
import csv
from pathlib import Path
import pickle

router = APIRouter()


# ----------------------------
# LAND ENDPOINTS
# ----------------------------

@router.post("/create-land/")
def create_land(land: Land):
    with get_session() as session:
        session.add(land)
        session.commit()
        session.refresh(land)
        return land


@router.get("/list-lands/")
def read_lands():
    with get_session() as session:
        return session.exec(select(Land)).all()


@router.get("/land/{land_id}/")
def get_land(land_id: int):
    with get_session() as session:
        land = session.get(Land, land_id)
        if not land:
            raise HTTPException(status_code=404, detail="Land not found")
        return land


# ----------------------------
# LAND FINANCE ENDPOINTS
# ----------------------------

@router.post("/land/{land_id}/add-finance/")
def add_finance_record(land_id: int, finance: LandFinance):
    with get_session() as session:
        land = session.get(Land, land_id)
        if not land:
            raise HTTPException(status_code=404, detail="Land not found")

        finance.land_id = land_id
        session.add(finance)
        session.commit()
        session.refresh(finance)
        return finance


@router.get("/land/{land_id}/finance-history/")
def get_finance_history(land_id: int):
    with get_session() as session:
        land = session.get(Land, land_id)
        if not land:
            raise HTTPException(status_code=404, detail="Land not found")

        finances = session.exec(
            select(LandFinance).where(LandFinance.land_id == land_id)
        ).all()
        return finances


# ----------------------------
# LANDMARK ENDPOINTS
# ----------------------------

@router.post("/create-landmark/")
def create_landmark(landmark: Landmark):
    with get_session() as session:
        session.add(landmark)
        session.commit()
        session.refresh(landmark)
        return landmark

@router.post("/bulk-create-lands/")
async def bulk_create_lands(file: UploadFile = File(...)):
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

    required_columns = {"name", "latitude", "longitude", "land_size", "dist_transit"}
    if not required_columns.issubset(df.columns):
        raise HTTPException(status_code=400, detail=f"CSV must contain columns: {required_columns}")

    lands = [
        Land(
            name=row["name"],
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            land_size=float(row["land_size"]),
            dist_transit=float(row["dist_transit"]),
        )
        for _, row in df.iterrows()
    ]

    with get_session() as session:
        session.add_all(lands)
        session.commit()

    return {"inserted": len(lands)}

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

@router.post("/bulk-create-land-finance/")
async def bulk_create_land_finance(file: UploadFile = File(...)):
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

    required_columns = {"land_id", "year", "land_price", "inflation", "interest_rate"}
    if not required_columns.issubset(df.columns):
        raise HTTPException(status_code=400, detail=f"CSV must contain columns: {required_columns}")

    finance_records = []
    for _, row in df.iterrows():
        finance_records.append(
            LandFinance(
                land_id=int(row["land_id"]),
                year=int(row["year"]),
                land_price=float(row["land_price"]),
                inflation=float(row["inflation"]),
                interest_rate=float(row["interest_rate"]),
            )
        )

    with get_session() as session:
        session.add_all(finance_records)
        session.commit()

    return {"inserted": len(finance_records)}


@router.get("/list-landmarks/")
def read_landmarks():
    with get_session() as session:
        return session.exec(select(Landmark)).all()


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
                result[landmark_type.value] = 0.0
                continue

            nearest = min(
                landmarks,
                key=lambda lm: haversine(land.latitude, land.longitude, lm.latitude, lm.longitude)
            )
            distance = haversine(land.latitude, land.longitude, nearest.latitude, nearest.longitude)
            result[landmark_type.value] = round(distance, 3)

        return result
    

@router.post("/land/generate-normalized-csv/")
def generate_normalized_land_csv():
    with get_session() as session:
        lands = session.exec(select(Land)).all()
        result_rows = []

        for land in lands:
            finance = session.exec(
                select(LandFinance)
                .where(LandFinance.land_id == land.id)
                .order_by(LandFinance.year.desc())
            ).first()

            if not finance:
                continue

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

            row = {
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
            }
            result_rows.append(row)

        # Save CSV next to main.py
        current_dir = Path(__file__).resolve().parent
        output_path = current_dir / "normalized_land_data.csv"

        with open(output_path, mode="w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=result_rows[0].keys())
            writer.writeheader()
            writer.writerows(result_rows)

        return {"status": "success", "file_path": str(output_path.name)}

@router.post("/train/land-price-model/")
def train_land_price_model():
    try:
        # Load normalized CSV
        df = pd.read_csv("normalized_land_data.csv")
        
        feature_cols = [
            "land_size", "dist_transit", "latitude", "longitude",
            "dist_cbd", "dist_bts", "dis_mrt", "dist_office",
            "dist_condo", "dist_tourist", "year", "land_price", "inflation", "interest_rate"
        ]
        
        if not all(col in df.columns for col in feature_cols):
            return {"error": "Missing one or more required columns in CSV."}

        X = df[feature_cols]
        y = df["land_price"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Save model
        with open("model.pkl", "wb") as f:
            pickle.dump(model, f)

        return {"status": "success", "message": "Model trained and saved as model.pkl"}
    
    except FileNotFoundError:
        return {"error": "normalized_land_data.csv not found. Please run CSV generation first."}
    except Exception as e:
        return {"error": str(e)}
    

@router.post("/predict/land-price/{land_id}")
def predict_land_price(land_id: int):
    import pandas as pd
    import pickle

    with get_session() as session:
        land = session.get(Land, land_id)
        if not land:
            raise HTTPException(status_code=404, detail="Land not found")

        finance = session.exec(
            select(LandFinance)
            .where(LandFinance.land_id == land.id)
            .order_by(LandFinance.year.desc())
        ).first()

        if not finance:
            raise HTTPException(status_code=400, detail="No finance data for land")

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
                key=lambda lm: haversine(land.latitude, land.longitude, lm.latitude, lm.longitude)
            )
            dist = haversine(land.latitude, land.longitude, nearest.latitude, nearest.longitude)
            dist_map[landmark_type.value] = round(dist, 4)

        # Create normalized input
        sample = {
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
        }

        # Predict with model
        try:
            with open("model.pkl", "rb") as f:
                model = pickle.load(f)
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="Trained model not found. Please train it first.")

        feature_cols = list(sample.keys())
        df_sample = pd.DataFrame([sample])
        predicted_price = model.predict(df_sample)[0]

        return {
            "normalized_input": sample,
            "predicted_land_price": round(predicted_price, 2)
        }
