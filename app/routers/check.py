from fastapi import APIRouter, HTTPException
from sqlmodel import select
from typing import List, Optional
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from app.db import get_session
from app.models import TempLand

router = APIRouter()

# 🔽 Response model WITHOUT images for list
class TempLandListOut(BaseModel):
    id: int
    landName: str
    area: float
    price: float
    address: str
    uploadedAt: str

    class Config:
        orm_mode = True

# 🔽 Response model WITH base64 images for detail view
class TempLandImageOut(BaseModel):
    id: int
    imageBase64: str

    class Config:
        orm_mode = True

class TempLandDetailOut(BaseModel):
    id: int
    landName: str
    description: str
    area: float
    price: float
    address: str
    latitude: float
    longitude: float
    zoning: Optional[str]
    popDensity: float
    floodRisk: str
    nearbyDevPlan: str
    uploadedAt: str
    images: List[TempLandImageOut]

    class Config:
        orm_mode = True

# 🔽 GET all temp lands (no images)
@router.get("/list", response_model=List[TempLandListOut])
def get_temp_lands():
    with get_session() as session:
        temp_lands = session.exec(select(TempLand)).all()
        return temp_lands

# 🔽 GET one temp land (with base64 images)
@router.get("/list/{id}", response_model=TempLandDetailOut)
def get_temp_land_by_id(id: int):
    with get_session() as session:
        statement = (
            select(TempLand)
            .where(TempLand.id == id)
            .options(selectinload(TempLand.images))  # ✅ eager-load relationship
        )
        temp_land = session.exec(statement).first()

        if not temp_land:
            raise HTTPException(status_code=404, detail="TempLand not found")

        return temp_land