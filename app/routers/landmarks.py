from fastapi import APIRouter, HTTPException, Request
from sqlmodel import select
from app.models import Land, Landmark
from app.db import get_session
from app.utils import haversine

router = APIRouter()

@router.get("/closest-landmarks/{land_id}")
def get_closest_landmarks(land_id: int):
    with get_session() as session:
        land = session.get(Land, land_id)

        if not land:
            raise HTTPException(status_code=404, detail="Land not found")

        landmarks = session.exec(select(Landmark)).all()

        distances = []
        for landmark in landmarks:
            distance = haversine(
                land.latitude, land.longitude,
                landmark.latitude, landmark.longitude
            )
            distances.append({
                "id": landmark.id,
                "type": landmark.type,
                "name": landmark.name,
                "latitude": landmark.latitude,
                "longitude": landmark.longitude,
                "distance_km": round(distance, 3)  # Round to 3 decimal places
            })

        # Sort by distance
        distances.sort(key=lambda x: x["distance_km"])

        # Take top 5
        closest = distances[:5]

        return closest