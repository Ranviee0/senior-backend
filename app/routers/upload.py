from fastapi import APIRouter, Form, File, UploadFile
from typing import List, Optional
from datetime import datetime
from app.db import get_session
from app.models import TempLand, TempLandImage
import base64
import json
from PIL import Image
from io import BytesIO


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

        if images:
            for image in images:
                # Read image bytes
                original_bytes = await image.read()

                # Open image with PIL
                try:
                    img = Image.open(BytesIO(original_bytes)).convert("RGBA")
                except Exception:
                    continue  # skip if image is not readable

                # Convert to PNG in memory
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)
                png_bytes = buffer.read()

                # Encode to base64
                image_base64 = base64.b64encode(png_bytes).decode("utf-8")

                temp_image = TempLandImage(
                    tempLandId=temp_land_id,
                    imageBase64=image_base64
                )
                session.add(temp_image)

        session.commit()

    return {"message": "Temporary upload successful", "temp_land_id": temp_land_id}
