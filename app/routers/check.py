from fastapi import APIRouter, HTTPException
from sqlmodel import select
from typing import List, Optional
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from app.db import get_session
from app.models import TempLand, TempLandImage, Land, LandImage
from PIL import Image
import base64
import os
from io import BytesIO

router = APIRouter()

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

@router.post("/publish/{temp_land_id}")
def publish_temp_land(temp_land_id: int):
    with get_session() as session:
        # Fetch TempLand with images
        stmt = (
            select(TempLand)
            .where(TempLand.id == temp_land_id)
            .options(selectinload(TempLand.images))
        )
        temp_land = session.exec(stmt).first()

        if not temp_land:
            raise HTTPException(status_code=404, detail="TempLand not found")

        # Create real Land
        new_land = Land(
            landName=temp_land.landName,
            description=temp_land.description,
            area=temp_land.area,
            price=temp_land.price,
            address=temp_land.address,
            latitude=temp_land.latitude,
            longitude=temp_land.longitude,
            zoning=temp_land.zoning,
            popDensity=temp_land.popDensity,
            floodRisk=temp_land.floodRisk,
            nearbyDevPlan=temp_land.nearbyDevPlan,
            uploadedAt=temp_land.uploadedAt,
        )
        session.add(new_land)
        session.commit()
        session.refresh(new_land)
        land_id = new_land.id

        # Decode and store each image
        for i, temp_img in enumerate(temp_land.images):
            try:
                # Decode base64 and convert to PNG
                img_bytes = base64.b64decode(temp_img.imageBase64)
                image = Image.open(BytesIO(img_bytes)).convert("RGBA")

                filename = f"land_{new_land.id}_{i + 1}.png"
                filepath = os.path.join(UPLOAD_DIR, filename)
                image.save(filepath, format="PNG")

                # Store path
                new_image = LandImage(
                    landId=new_land.id,
                    imagePath=f"/{UPLOAD_DIR}/{filename}"
                )
                session.add(new_image)
            except Exception as e:
                print(f"Failed to process image {i + 1}: {e}")
                continue

        session.commit()

        # Optional: clean up temp entries
        for temp_img in temp_land.images:
            session.delete(temp_img)
        session.delete(temp_land)
        session.commit()

    return {"message": "Land published successfully", "land_id": land_id}

@router.delete("/reject/{temp_land_id}")
def reject_temp_land(temp_land_id: int):
    with get_session() as session:
        stmt = (
            select(TempLand)
            .where(TempLand.id == temp_land_id)
            .options(selectinload(TempLand.images))
        )
        temp_land = session.exec(stmt).first()

        if not temp_land:
            raise HTTPException(status_code=404, detail="TempLand not found")

        # Delete associated images
        for img in temp_land.images:
            session.delete(img)

        # Delete the TempLand itself
        session.delete(temp_land)
        session.commit()

    return {"message": f"TempLand {temp_land_id} has been rejected and deleted."}
