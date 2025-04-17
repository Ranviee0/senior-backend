from typing import List, Optional
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship


class LandmarkType(str, Enum):
    MRT = "MRT"
    BTS = "BTS"
    CBD = "CBD"
    Office = "Office"
    Condo = "Condo"
    Tourist = "Tourist"


class Land(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    latitude: float
    longitude: float
    land_size: float  # in square wah or sqm
    dist_transit: float  # distance to nearest transit in km

    finance_history: List["LandFinance"] = Relationship(back_populates="land")


class LandFinance(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    land_id: int = Field(foreign_key="land.id")
    year: int
    land_price: float  # price per unit (e.g. million THB per rai)
    inflation: float
    interest_rate: float

    land: Land = Relationship(back_populates="finance_history")


class Landmark(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    type: str  # could also use LandmarkType enum
    name: str
    latitude: float
    longitude: float

class Normalized(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Land characteristics
    land_size: float
    dist_transit: float
    latitude: float
    longitude: float

    # Landmark distances
    dist_cbd: float
    dist_bts: float
    dist_mrt: float
    dist_office: float
    dist_condo: float
    dist_tourist: float

    # Financial information
    year: int
    land_price: float
    inflation: float
    interest_rate: float
