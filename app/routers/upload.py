from fastapi import APIRouter, Form, File, UploadFile
from typing import List, Optional
from sqlmodel import select
from app.db import get_session
from app.models import Land, LandImage
from datetime import datetime
import os
import json

router = APIRouter()

UPLOAD_DIR = "uploaded_files"  # make sure this folder exists

@router.post("/")
async def upload(
    land_name: str = Form(...),
    description: str = Form(...),
    area: float = Form(...),
    price: float = Form(...),
    address: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    zoning: Optional[str] = Form(None),
    pop_density: float = Form(...),
    flood_risk: str = Form(...),
    nearby_dev_plan: List[str] = Form(...),
    images: Optional[List[UploadFile]] = File(None)
):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    with get_session() as session:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        new_land = Land(
            landName=land_name,
            description=description,
            area=area,
            price=price,
            address=address,
            latitude=latitude,
            longitude=longitude,
            zoning=zoning,
            popDensity=pop_density,
            floodRisk=flood_risk,
            nearbyDevPlan=json.dumps(nearby_dev_plan, ensure_ascii=False),
            uploadedAt=timestamp,
        )
        session.add(new_land)
        session.commit()
        session.refresh(new_land)  # ✅ this ensures ID is populated

        land_id = new_land.id   # ✅ Save id BEFORE session closes

        if images:
            for i, image in enumerate(images):
                ext = os.path.splitext(image.filename)[-1]
                filename = f"{timestamp}_{i+1}{ext}"
                file_path = os.path.join(UPLOAD_DIR, filename)

                with open(file_path, "wb") as f:
                    f.write(await image.read())

            new_image = LandImage(
                landId=land_id,
                imagePath=f"/{UPLOAD_DIR}/{filename}"
            )
            session.add(new_image)

        session.commit()

    # 🔥 Now session is closed, but land_id is safe
    return {"message": "Upload successful", "land_id": land_id}
