from fastapi import APIRouter, HTTPException, UploadFile, File
from app.db import get_session
from app.models import Land, Landmark, LandFinance
import pandas as pd
import io

router = APIRouter()

@router.post("/lands/")
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

@router.post("/landmarks/")
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

@router.post("/finance/")
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

