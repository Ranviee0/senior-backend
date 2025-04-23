from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.db import get_session
from app.models import Land, LandFinance

router = APIRouter()

@router.post("/{land_id}/add")
def add_finance_record(land_id: int, finance: LandFinance):
    with get_session() as session:
        land = session.get(Land, land_id)
        if not land:
            raise HTTPException(status_code=404, detail="Land not found")

        finance.land_id = land_id
        session.add(finance)
        session.commit()
        session.refresh(finance)
        return finance

@router.get("/{land_id}/")
def get_finance_history(land_id: int):
    with get_session() as session:
        land = session.get(Land, land_id)
        if not land:
            raise HTTPException(status_code=404, detail="Land not found")

        return session.exec(
            select(LandFinance).where(LandFinance.land_id == land_id)
        ).all()

