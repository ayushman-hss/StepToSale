from pydantic import BaseModel
from typing import List, Optional

class Kpis(BaseModel):
    total_footfall: int
    total_sales: float
    total_transactions: int
    conversion_rate: float
    avg_basket: float
    sales_per_visitor: float

class HourlyPoint(BaseModel):
    hour: int
    footfall: int
    sales: float
    transactions: int
    conversion: float

class DailyPoint(BaseModel):
    date: str
    footfall: int
    sales: float
    transactions: int
    conversion: float

class UploadResponse(BaseModel):
    upload_id: int
    rows: int
    stores: List[str]
    date_range: List[str]

class StoreOut(BaseModel):
    code: str
    name: str

class HeatmapPoint(BaseModel):
    dow: int
    hour: int
    footfall: int

class Insight(BaseModel):
    kind: str      # warning | opportunity | observation | win
    text: str

class DashboardResponse(BaseModel):
    kpis: Kpis
    hourly: List[HourlyPoint]
    daily: List[DailyPoint]
    insights: List[Insight] 
    whatsapp: str
    heatmap: List[HeatmapPoint]