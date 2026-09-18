from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class Store(SQLModel, table=True):
    __tablename__ = "store"
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)   # "S1", "S2"
    name: str = ""

class Upload(SQLModel, table=True):
    __tablename__ = "upload"
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    rows: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

class HourlyData(SQLModel, table=True):
    __tablename__ = "hourly_data"
    id: Optional[int] = Field(default=None, primary_key=True)
    store_id: int = Field(foreign_key="store.id", index=True)
    upload_id: int = Field(foreign_key="upload.id", index=True)
    date: str = Field(index=True)     # YYYY-MM-DD
    hour: int = Field(index=True)     # 0-23
    footfall: int
    transactions: int
    sales: float