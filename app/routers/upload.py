from fastapi import APIRouter, Form, File, UploadFile
from typing import List, Optional
from app.db import get_session
from app.models import TempLand, TempLandImage  # 👈 Use the TEMP models
from datetime import datetime
import base64
import json

router = APIRouter()


@router.post("/temp-upload/")
async def upload_temp_land(
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
        new_temp_land = TempLand(
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
        session.add(new_temp_land)
        session.commit()
        session.refresh(new_temp_land)

        temp_land_id = new_temp_land.id

        # Handle base64 image encoding
        if images:
            for image in images:
                image_bytes = await image.read()
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")

                temp_image = TempLandImage(
                    tempLandId=temp_land_id,
                    imageBase64=image_base64
                )
                session.add(temp_image)

        session.commit()

    return {"message": "Temporary upload successful", "temp_land_id": temp_land_id}
