from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from config import PASSTHROUGH_COLUMNS
from normalizers import (
    normalize_address,
    normalize_company_name,
    normalize_customer_name,
    normalize_phone,
    normalize_sido,
    normalize_sigungu,
)
from scorers import (
    calc_base_score,
    calc_bonus,
    calc_final_score,
    classify_company_match,
    classify_customer_match,
    score_address,
    score_company_name,
    score_customer_exact,
    score_phone,
    score_sido,
    score_sigungu,
)


@dataclass
class CandidateResult:
    b_index: int
    company_score: float
    sido_score: float
    sigungu_score: float
    phone_score: float
    address_score: float
    base_score: float
    bonus: float
    final_score: float
    customer_matched: bool
    company_match_status: str
    customer_match_status: str


def _prepare_b_records(
    df_b: pd.DataFrame,
    remove_words: Sequence[str],
    sido_alias: Dict[str, str],
) -> List[dict]:
    records: List[dict] = []
    for idx, row in df_b.iterrows():
        records.append(
            {
                "index": idx,
                "raw": row,
                "company": normalize_company_name(row["거래처명"], remove_words),
                "sido": normalize_sido(row["시도명"], sido_alias),
                "sigungu": normalize_sigungu(row["시군구명"]),
                "address": normalize_address(row["도로명주소"]),
                "phone": normalize_phone(row["전화번호"]),
                "customer": normalize_customer_name(row["고객명"]),
            }
        )
    return records


def _prepare_a_record(
    row: pd.Series,
    remove_words: Sequence[str],
    sido_alias: Dict[str, str],
) -> dict:
    return {
        "raw": row,
        "company": normalize_company_name(row["거래처명"], remove_words),
        "sido": normalize_sido(row["시도명"], sido_alias),
        "sigungu": normalize_sigungu(row["시군구명"]),
        "address": normalize_address(row["도로명주소"]),
        "phone": normalize_phone(row["전화번호"]),
        "customer": normalize_customer_name(row["고객명"]),
    }


def _score_candidate(a_record: dict, b_record: dict) -> CandidateResult:
    company_score = score_company_name(a_record["company"], b_record["company"])
    sido_score = score_sido(a_record["sido"], b_record["sido"])
    sigungu_score = score_sigungu(a_record["sigungu"], b_record["sigungu"])
    phone_score = score_phone(
        a_record["phone"],
        b_record["phone"],
        a_record["sido"],
        b_record["sido"],
    )
    address_score = score_address(a_record["address"], b_record["address"])
    base_score = calc_base_score(
        company_score,
        sido_score,
        sigungu_score,
        phone_score,
        address_score,
    )
    customer_matched = score_customer_exact(a_record["customer"], b_record["customer"])
    bonus = calc_bonus(base_score, customer_matched)
    final_score = calc_final_score(base_score, bonus)

    return CandidateResult(
        b_index=b_record["index"],
        company_score=company_score,
        sido_score=sido_score,
        sigungu_score=sigungu_score,
        phone_score=phone_score,
        address_score=address_score,
        base_score=base_score,
        bonus=bonus,
        final_score=final_score,
        customer_matched=customer_matched,
        company_match_status=classify_company_match(final_score),
        customer_match_status=classify_customer_match(customer_matched),
    )


def _candidate_sort_key(result: CandidateResult) -> Tuple:
    return (
        result.final_score,
        1 if result.customer_matched else 0,
        result.phone_score,
        result.company_score,
        result.address_score,
    )


def _select_candidates(
    a_record: dict,
    b_records: Sequence[dict],
) -> List[CandidateResult]:
    same_sido = [record for record in b_records if record["sido"] and record["sido"] == a_record["sido"]]
    target_records = same_sido if same_sido else list(b_records)

    results = [_score_candidate(a_record, b_record) for b_record in target_records]
    results.sort(key=_candidate_sort_key, reverse=True)
    return results


def _pick_near_candidates(
    all_results: List[CandidateResult],
    representative: Optional[CandidateResult],
    max_count: int = 3,
    score_gap: float = 5.0,
) -> List[CandidateResult]:
    if representative is None:
        return []

    near: List[CandidateResult] = []
    for result in all_results:
        if result.b_index == representative.b_index:
            continue
        if representative.final_score - result.final_score <= score_gap:
            near.append(result)
        if len(near) >= max_count:
            break
    return near


def _format_row_columns(row: pd.Series, prefix: str) -> dict:
    return {f"{prefix}{col}": row.get(col, "") for col in PASSTHROUGH_COLUMNS}


def _empty_row_columns(prefix: str) -> dict:
    return {f"{prefix}{col}": "" for col in PASSTHROUGH_COLUMNS}


def _build_output_row(
    a_row: pd.Series,
    representative: Optional[CandidateResult],
    near_candidates: Sequence[CandidateResult],
    df_b: pd.DataFrame,
) -> dict:
    output = _format_row_columns(a_row, "(A)")

    if representative is None:
        output.update(_empty_row_columns("(B)"))
        output.update(
            {
                "거래처 기본 유사도점수": 0,
                "고객명 가점": 0,
                "거래처 최종 유사도점수": 0,
                "거래처 일치여부": "미매칭",
                "고객명 일치여부": "불일치",
            }
        )
    else:
        b_row = df_b.loc[representative.b_index]
        output.update(_format_row_columns(b_row, "(B)"))
        output.update(
            {
                "거래처 기본 유사도점수": representative.base_score,
                "고객명 가점": representative.bonus,
                "거래처 최종 유사도점수": representative.final_score,
                "거래처 일치여부": representative.company_match_status,
                "고객명 일치여부": representative.customer_match_status,
            }
        )

    for idx in range(1, 4):
        prefix = f"근접후보{idx}_"
        if idx - 1 < len(near_candidates):
            near = near_candidates[idx - 1]
            near_row = df_b.loc[near.b_index]
            output.update(_format_row_columns(near_row, f"{prefix}(B)"))
            output[f"{prefix}거래처 최종 유사도점수"] = near.final_score
        else:
            output.update(_empty_row_columns(f"{prefix}(B)"))
            output[f"{prefix}거래처 최종 유사도점수"] = ""

    return output


def match_dataframes(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    remove_words: Iterable[str],
    sido_alias: Dict[str, str],
    progress_callback=None,
) -> pd.DataFrame:
    b_records = _prepare_b_records(df_b, remove_words, sido_alias)
    output_rows: List[dict] = []
    total = len(df_a)

    for row_number, (_, a_row) in enumerate(df_a.iterrows(), start=1):
        a_record = _prepare_a_record(a_row, remove_words, sido_alias)
        scored = _select_candidates(a_record, b_records)
        representative = scored[0] if scored else None
        near_candidates = _pick_near_candidates(scored, representative)
        output_rows.append(_build_output_row(a_row, representative, near_candidates, df_b))

        if progress_callback:
            progress_callback(row_number, total)

    def prefixed_columns(label: str) -> List[str]:
        return [f"{label}{col}" for col in PASSTHROUGH_COLUMNS]

    columns = (
        prefixed_columns("(A)")
        + prefixed_columns("(B)")
        + [
            "거래처 기본 유사도점수",
            "고객명 가점",
            "거래처 최종 유사도점수",
            "거래처 일치여부",
            "고객명 일치여부",
        ]
    )
    for idx in range(1, 4):
        columns.extend(prefixed_columns(f"근접후보{idx}_(B)"))
        columns.append(f"근접후보{idx}_거래처 최종 유사도점수")

    return pd.DataFrame(output_rows, columns=columns)
