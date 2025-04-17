# models.py
from typing import List, Optional
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship


class LandmarkType(str, Enum):
    MRT = "MRT"
    BTS = "BTS"


class Land(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    latitude: float
    longitude: float
    land_size: float

    prices: List["LandPriceHistory"] = Relationship(back_populates="land")


class LandPriceHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    land_id: int = Field(foreign_key="land.id")
    year: int
    price_per_sqm: float

    land: Land = Relationship(back_populates="prices")


class Landmark(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    type: str
    name: str
    latitude: float
    longitude: float
