import numpy as np
import pandas as pd


def load_and_process_data(file_path: str) -> pd.DataFrame:
    """
    Load csv and normalize columns to:
    Date index, Open/High/Low/Close/Volume.
    Accepts either:
      - time/open/high/low/close/volume
      - Date/Open/High/Low/Close/Volume
    """
    df = pd.read_csv(file_path)

    # normalize column names
    rename_map = {
        "time": "Date",
        "DateTime": "Date",
        "date": "Date",
        "datetime": "Date",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
    }
    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

    required = {"Date", "Open", "High", "Low", "Close", "Volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
    df.set_index("Date", inplace=True)
    return df


def calculate_indicators(df: pd.DataFrame, length: int = 21) -> pd.DataFrame:
    """
    Compute indicators and trading filters.
    This mirrors the user's research code but keeps only what the strategy uses.
    """
    df = df.copy()
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # EMA (XMA)
    df["XMA"] = close.ewm(span=length, adjust=False).mean()

    # TRIMA (SMA of SMA)
    n = int(np.ceil((length + 1) / 2))
    sma1 = close.rolling(window=n).mean()
    df["TRIMA"] = sma1.rolling(window=n).mean()

    # Regime MA
    df["SMA_200"] = close.rolling(window=200).mean()

    # ATR
    df["TR"] = np.maximum(
        high - low,
        np.maximum(abs(high - close.shift(1)), abs(low - close.shift(1))),
    )
    df["ATR"] = df["TR"].rolling(window=14).mean()
    df["ATR_Prev"] = df["ATR"].shift(1)

    # Momentum
    df["Mom_1"] = close.pct_change(1) * 100
    df["Mom_2"] = close.pct_change(2) * 100

    # Signals (filters baked in)
    df["CrossUp"] = (
        (df["XMA"] > df["TRIMA"])
        & (df["XMA"].shift(1) <= df["TRIMA"].shift(1))
        & (df["Mom_2"] > -0.25)
        & (df["Mom_1"] > -0.25)
    )

    df["CrossDown"] = (
        (df["XMA"] < df["TRIMA"])
        & (df["XMA"].shift(1) >= df["TRIMA"].shift(1))
        & (close < df["SMA_200"])
    )

    return df
