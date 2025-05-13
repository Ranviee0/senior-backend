from fastapi import APIRouter
from sqlmodel import select
from typing import List
from app.db import get_session
from app.models import TempLand

router = APIRouter()

@router.get("/list")
def get_temp_lands():
    with get_session() as session:
        temp_lands = session.exec(select(TempLand)).all()
        return temp_lands

