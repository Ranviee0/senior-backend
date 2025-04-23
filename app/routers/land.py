from fastapi import APIRouter, HTTPException
from app.models import Land
from app.db import get_session
from sqlmodel import select

router = APIRouter()

@router.post("/create/")
def create_land(land: Land):
    with get_session() as session:
        session.add(land)
        session.commit()
        session.refresh(land)
        return land

@router.get("/")
def read_lands():
    with get_session() as session:
        return session.exec(select(Land)).all()

@router.get("/{land_id}/")
def get_land(land_id: int):
    with get_session() as session:
        land = session.get(Land, land_id)
        if not land:
            raise HTTPException(status_code=404, detail="Land not found")
        return land
