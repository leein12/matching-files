from __future__ import annotations

import re
from typing import Dict, Iterable

import pandas as pd


NON_WORD_PATTERN = re.compile(r"[^\w가-힣]")
SIGUNGU_SUFFIX_PATTERN = re.compile(r"(시|군|구)$")


def safe_str(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def remove_spaces_and_symbols(text: str) -> str:
    compact = re.sub(r"\s+", "", text.strip())
    return NON_WORD_PATTERN.sub("", compact)


def normalize_company_name(value: object, remove_words: Iterable[str]) -> str:
    text = remove_spaces_and_symbols(safe_str(value))
    for word in remove_words:
        token = remove_spaces_and_symbols(safe_str(word))
        if token:
            text = text.replace(token, "")
    return text


def normalize_sido(value: object, sido_alias: Dict[str, str]) -> str:
    raw = remove_spaces_and_symbols(safe_str(value))
    return sido_alias.get(raw, raw)


def normalize_sigungu(value: object) -> str:
    text = remove_spaces_and_symbols(safe_str(value))
    return SIGUNGU_SUFFIX_PATTERN.sub("", text)


def normalize_phone(value: object) -> str:
    return re.sub(r"\D", "", safe_str(value))


def normalize_address(value: object) -> str:
    return remove_spaces_and_symbols(safe_str(value))


def normalize_customer_name(value: object) -> str:
    return remove_spaces_and_symbols(safe_str(value))
