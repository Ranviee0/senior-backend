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
    landName: str
    description: str
    area: float
    price: float
    address: str
    latitude: float
    longitude: float
    zoning: Optional[str]
    popDensity: float
    floodRisk: str
    nearbyDevPlan: str  # store as JSON string
    uploadedAt: str

    images: List["LandImage"] = Relationship(back_populates="land")

class LandImage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    landId: int = Field(foreign_key="land.id")
    imagePath: str  # relative path to file (can use as URL)

    land: Optional[Land] = Relationship(back_populates="images")

class TempLand(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    landName: str
    description: str
    area: float
    price: float
    address: str
    latitude: float
    longitude: float
    zoning: Optional[str] = None
    popDensity: float
    floodRisk: str
    nearbyDevPlan: str  # store as JSON string
    uploadedAt: str

    # One-to-many relationship to TempLandImage
    images: List["TempLandImage"] = Relationship(back_populates="tempLand")


class TempLandImage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tempLandId: int = Field(foreign_key="templand.id")
    imageBase64: str  # Base64-encoded image string for preview

    # Backref to parent TempLand
    tempLand: Optional[TempLand] = Relationship(back_populates="images")

class Landmark(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    type: str  # could also use LandmarkType enum
    name: str
    latitude: float
    longitude: float
