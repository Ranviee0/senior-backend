from fastapi import APIRouter, Request, Query
from app.db import get_session
from typing import List, Optional
from app.models import Land, LandImage
from sqlmodel import select
from pydantic import BaseModel

router = APIRouter()

class LandReadWithImages(BaseModel):
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
    images: List[str]  # <<--- List of URLs

    class Config:
        orm_mode = True


@router.get("/", response_model=List[LandReadWithImages])
def get_lands(request: Request):
    with get_session() as session:
        lands = session.exec(select(Land)).all()

        base_url = str(request.base_url).rstrip("/")

        result = []
        for land in lands:
            # 🚀 Fetch LandImage objects
            images = session.exec(
                select(LandImage).where(LandImage.landId == land.id)
            ).all()

            # 🚀 Correctly use image.imagePath
            image_paths = [
                f"{base_url}{image.imagePath}" if image.imagePath.startswith("/") else f"{base_url}/{image.imagePath}"
                for image in images
            ]

            result.append(LandReadWithImages(
                id=land.id,
                landName=land.landName,
                description=land.description,
                area=land.area,
                price=land.price,
                address=land.address,
                latitude=land.latitude,
                longitude=land.longitude,
                zoning=land.zoning,
                popDensity=land.popDensity,
                floodRisk=land.floodRisk,
                nearbyDevPlan=land.nearbyDevPlan,
                uploadedAt=land.uploadedAt,
                images=image_paths
            ))

        return result
    
from fastapi import HTTPException


@router.get("/search", response_model=List[LandReadWithImages])
def search_lands(
    request: Request,
    province: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
):
    with get_session() as session:
        query = select(Land)
        all_lands = session.exec(query).all()

        filtered_lands = []

        for land in all_lands:
            matches_province = True
            matches_name = True

            # ✅ Province filter
            if province:
                address_parts = [part.strip() for part in land.address.split(",")]
                province_text = address_parts[-2] if len(address_parts) >= 2 else address_parts[-1]
                matches_province = province.lower() in province_text.lower()

            # ✅ Land name filter
            if name:
                matches_name = name.lower() in land.landName.lower()

            if matches_province and matches_name:
                filtered_lands.append(land)

        base_url = str(request.base_url).rstrip("/")
        result = []
        for land in filtered_lands:
            images = session.exec(
                select(LandImage).where(LandImage.landId == land.id)
            ).all()

            image_paths = [
                f"{base_url}{image.imagePath}" if image.imagePath.startswith("/") else f"{base_url}/{image.imagePath}"
                for image in images
            ]

            result.append(LandReadWithImages(
                id=land.id,
                landName=land.landName,
                description=land.description,
                area=land.area,
                price=land.price,
                address=land.address,
                latitude=land.latitude,
                longitude=land.longitude,
                zoning=land.zoning,
                popDensity=land.popDensity,
                floodRisk=land.floodRisk,
                nearbyDevPlan=land.nearbyDevPlan,
                uploadedAt=land.uploadedAt,
                images=image_paths
            ))

        return result
    

@router.get("/{land_id}", response_model=LandReadWithImages)
def get_land_by_id(land_id: int, request: Request):
    with get_session() as session:
        land = session.get(Land, land_id)

        if not land:
            raise HTTPException(status_code=404, detail="Land not found")

        images = session.exec(
            select(LandImage).where(LandImage.landId == land.id)
        ).all()

        base_url = str(request.base_url).rstrip("/")

        image_paths = [
            f"{base_url}{image.imagePath}" if image.imagePath.startswith("/") else f"{base_url}/{image.imagePath}"
            for image in images
        ]

        return LandReadWithImages(
            id=land.id,
            landName=land.landName,
            description=land.description,
            area=land.area,
            price=land.price,
            address=land.address,
            latitude=land.latitude,
            longitude=land.longitude,
            zoning=land.zoning,
            popDensity=land.popDensity,
            floodRisk=land.floodRisk,
            nearbyDevPlan=land.nearbyDevPlan,
            uploadedAt=land.uploadedAt,
            images=image_paths
        )
