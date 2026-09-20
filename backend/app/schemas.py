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

class ProductIn(BaseModel):
    sku: str
    name: str
    cost_price: float
    sell_price: float


class ProductOut(ProductIn):
    id: int
    margin_pct: float


class BundleSuggestionOut(BaseModel):
    id: int
    sku_a: str
    sku_b: str
    name_a: str
    name_b: str
    transactions_with_both: int
    total_transactions: int
    confidence: float
    lift: float
    separate_price: float
    separate_margin_pct: float
    suggested_price: float
    suggested_margin_pct: float
    margin_floor_pct: float
    status: str
    approved_price: Optional[float]


class BundleActionIn(BaseModel):
    price: Optional[float] = None