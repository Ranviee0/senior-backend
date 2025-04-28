# utils.py

from math import radians, cos, sin, asin, sqrt
from app.models import Landmark, LandmarkType
from sqlmodel import select
from pydantic import BaseModel

class PredictBody(BaseModel):
    land_size: float
    latitude: float
    longitude: float
    dist_transit: float
    dist_mrt: float
    dist_bts: float
    dist_cbd: float
    dist_office: float
    dist_condo: float
    dist_tourist: float

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth (in kilometers).
    """
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))

    return R * c

def compute_distance_map(session, land):
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

    return dist_map

def create_prediction_object(session, land):
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

    # After dist_map is ready
    dist_mrt = dist_map.get('MRT', 0.0)
    dist_bts = dist_map.get('BTS', 0.0)
    dist_transit = min(dist_mrt, dist_bts)

    predict_body = PredictBody(
        land_size=land.land_size,
        latitude=land.latitude,
        longitude=land.longitude,
        dist_transit=dist_transit,
        dist_mrt=dist_mrt,
        dist_bts=dist_bts,
        dist_cbd=dist_map.get('CBD', 0.0),
        dist_office=dist_map.get('Office', 0.0),
        dist_condo=dist_map.get('Condo', 0.0),
        dist_tourist=dist_map.get('Tourist', 0.0),
    )

    return predict_body