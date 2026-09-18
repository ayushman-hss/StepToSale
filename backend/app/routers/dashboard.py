from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from sqlmodel import Session, select
from typing import Optional
import pandas as pd

from ..db import get_session
from ..models import Store, Upload, HourlyData
from ..schemas import DashboardResponse, UploadResponse, StoreOut
from ..services.parser import parse_excel
from ..services.insights import generate_insights, whatsapp_summary
from ..services.metrics import compute_kpis, hourly_series, daily_series, heatmap_series


router = APIRouter(prefix="/api", tags=["dashboard"])


@router.post("/upload", response_model=UploadResponse)
async def upload(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Only .xlsx or .xls files are accepted")

    try:
        df = parse_excel(file.file)
    except Exception as e:
        raise HTTPException(400, f"Parse error: {e}")

    if df.empty:
        raise HTTPException(400, "No valid rows found")

    # 1. Upsert stores
    store_codes = sorted(df["store_id"].unique().tolist())
    existing = {
        s.code: s
        for s in session.exec(select(Store).where(Store.code.in_(store_codes))).all()
    }
    for code in store_codes:
        if code not in existing:
            s = Store(code=code, name=code)
            session.add(s)
            session.flush()
            existing[code] = s

    # 2. Register upload
    upload = Upload(filename=file.filename, rows=len(df))
    session.add(upload)
    session.flush()

    # 3. Bulk insert rows
    records = df.to_dict(orient="records")
    session.add_all([
        HourlyData(
            store_id=existing[r["store_id"]].id,
            upload_id=upload.id,
            date=r["date"],
            hour=int(r["hour"]),
            footfall=int(r["footfall"]),
            transactions=int(r["transactions"]),
            sales=float(r["sales"]),
        )
        for r in records
    ])
    session.commit()

    return UploadResponse(
        upload_id=upload.id,
        rows=len(records),
        stores=store_codes,
        date_range=[df["date"].min(), df["date"].max()],
    )


def _load_df(
    session: Session,
    store_code: Optional[str],
    start: Optional[str],
    end: Optional[str],
) -> pd.DataFrame:
    stmt = (
        select(
            HourlyData.date,
            HourlyData.hour,
            HourlyData.footfall,
            HourlyData.transactions,
            HourlyData.sales,
            Store.code.label("store_id"),
        )
        .join(Store, Store.id == HourlyData.store_id)
    )

    if store_code and store_code != "all":
        stmt = stmt.where(Store.code == store_code)
    if start:
        stmt = stmt.where(HourlyData.date >= start)
    if end:
        stmt = stmt.where(HourlyData.date <= end)

    rows = session.exec(stmt).all()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r._mapping) for r in rows])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    store_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    session: Session = Depends(get_session),
):
    df = _load_df(session, store_id, start_date, end_date)
    if df.empty:
        raise HTTPException(404, "No data for the given filters")

    return DashboardResponse(
        kpis=compute_kpis(df),
        hourly=hourly_series(df),
        daily=daily_series(df),
        heatmap=heatmap_series(df),
        insights=generate_insights(df),
        whatsapp=whatsapp_summary(df),
    )


@router.get("/stores", response_model=list[StoreOut])
def list_stores(session: Session = Depends(get_session)):
    stores = session.exec(select(Store).order_by(Store.code)).all()
    return [StoreOut(code=s.code, name=s.name) for s in stores]


@router.get("/health")
def health(session: Session = Depends(get_session)):
    has_data = session.exec(select(HourlyData).limit(1)).first() is not None
    return {"ok": True, "has_data": has_data}