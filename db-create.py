from sqlmodel import Field, SQLModel, Relationship, create_engine, Session
from typing import List, Optional

class Land(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    latitude: float
    longitude: float
    land_size: float
    age: Optional[int] = None

    # Relationship to LandPriceHistory
    prices: List["LandPriceHistory"] = Relationship(back_populates="land")

class LandPriceHistory(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    land_id: int = Field(foreign_key="land.id")  # Foreign Key
    year: int  # Example: 2025, 2024, 2023...
    price_per_sqm: float  # Price per square meter

    # Relationship back to Land
    land: Land = Relationship(back_populates="prices")

class Landmarks(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    type: str
    name: str
    latitude: float
    longitude: float

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

SQLModel.metadata.create_all(engine)