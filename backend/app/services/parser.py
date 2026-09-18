import pandas as pd
from typing import BinaryIO

REQUIRED = {"date", "hour", "footfall", "transactions", "sales"}

def parse_excel(file: BinaryIO) -> pd.DataFrame:
    df = pd.read_excel(file)
    df.columns = [str(c).strip().lower() for c in df.columns]

    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["hour"] = df["hour"].astype(int)
    df["footfall"] = df["footfall"].astype(int)
    df["transactions"] = df["transactions"].astype(int)
    df["sales"] = df["sales"].astype(float)

    if "store_id" not in df.columns:
        df["store_id"] = "S1"
    else:
        df["store_id"] = df["store_id"].astype(str)

    # Drop invalid rows rather than failing the whole upload
    df = df[(df["hour"] >= 0) & (df["hour"] <= 23)]
    df = df[df["footfall"] >= 0]
    df = df[df["transactions"] >= 0]

    return df.reset_index(drop=True)