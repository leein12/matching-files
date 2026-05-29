from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


REQUIRED_COLUMNS = [
    "거래처명",
    "시도명",
    "시군구명",
    "도로명주소",
    "전화번호",
    "고객명",
]


DEFAULT_SIDO_ALIAS = {
    "서울특별시": "서울",
    "서울시": "서울",
    "서울": "서울",
    "부산광역시": "부산",
    "부산시": "부산",
    "부산": "부산",
    "대구광역시": "대구",
    "대구시": "대구",
    "대구": "대구",
    "인천광역시": "인천",
    "인천시": "인천",
    "인천": "인천",
    "광주광역시": "광주",
    "광주시": "광주",
    "광주": "광주",
    "대전광역시": "대전",
    "대전시": "대전",
    "대전": "대전",
    "울산광역시": "울산",
    "울산시": "울산",
    "울산": "울산",
    "세종특별자치시": "세종",
    "세종시": "세종",
    "세종": "세종",
    "경기도": "경기",
    "경기": "경기",
    "강원특별자치도": "강원",
    "강원도": "강원",
    "강원": "강원",
    "충청북도": "충북",
    "충북": "충북",
    "충청남도": "충남",
    "충남": "충남",
    "전북특별자치도": "전북",
    "전라북도": "전북",
    "전북": "전북",
    "전라남도": "전남",
    "전남": "전남",
    "경상북도": "경북",
    "경북": "경북",
    "경상남도": "경남",
    "경남": "경남",
    "제주특별자치도": "제주",
    "제주도": "제주",
    "제주": "제주",
}


DEFAULT_COMPANY_REMOVE_WORDS = [
    "학교법인",
    "의료법인",
    "재단법인",
    "사회복지법인",
    "주식회사",
    "(주)",
    "㈜",
    "법인",
]


@dataclass(frozen=True)
class AppPaths:
    base_dir: Path
    input_dir: Path
    output_dir: Path
    logs_dir: Path
    rules_dir: Path
    input_a_path: Path
    input_b_path: Path
    output_c_path: Path
    sido_alias_path: Path
    company_remove_words_path: Path


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def build_paths() -> AppPaths:
    base_dir = get_base_dir()
    input_dir = base_dir / "input"
    output_dir = base_dir / "output"
    logs_dir = base_dir / "logs"
    rules_dir = base_dir / "rules"
    return AppPaths(
        base_dir=base_dir,
        input_dir=input_dir,
        output_dir=output_dir,
        logs_dir=logs_dir,
        rules_dir=rules_dir,
        input_a_path=input_dir / "A.xlsx",
        input_b_path=input_dir / "B.xlsx",
        output_c_path=output_dir / "C.xlsx",
        sido_alias_path=rules_dir / "sido_alias.json",
        company_remove_words_path=rules_dir / "company_remove_words.json",
    )
