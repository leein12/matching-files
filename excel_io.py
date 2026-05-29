from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


def load_excel(path: Path) -> pd.DataFrame:
    return pd.read_excel(path, engine="openpyxl")


def save_excel(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False, engine="openpyxl")


def validate_required_columns(df: pd.DataFrame, required_columns: Iterable[str], file_label: str) -> None:
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"{file_label} 파일에 필수 컬럼이 누락되었습니다: {joined}")
