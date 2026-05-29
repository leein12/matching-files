from __future__ import annotations

from rapidfuzz import fuzz


def score_company_name(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    token_set = fuzz.token_set_ratio(a, b)
    partial = fuzz.partial_ratio(a, b)
    return float(max(token_set, partial))


def score_sido(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return 100.0 if a == b else 0.0


def score_sigungu(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return float(fuzz.ratio(a, b))


def score_address(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return float(fuzz.partial_ratio(a, b))


def score_phone(a_phone: str, b_phone: str, a_sido: str, b_sido: str) -> float:
    if not a_phone or not b_phone:
        return 0.0
    if a_phone == b_phone:
        return 100.0
    if a_sido and b_sido and a_sido == b_sido:
        if a_phone.endswith(b_phone) or b_phone.endswith(a_phone):
            return 100.0
    if len(a_phone) >= 4 and len(b_phone) >= 4 and a_phone[-4:] == b_phone[-4:]:
        return 70.0
    return 0.0


def score_customer_exact(a_customer: str, b_customer: str) -> bool:
    if not a_customer or not b_customer:
        return False
    return a_customer == b_customer


def calc_base_score(
    company_score: float,
    sido_score: float,
    sigungu_score: float,
    phone_score: float,
    address_score: float,
) -> float:
    score = (
        company_score * 0.45
        + sido_score * 0.15
        + sigungu_score * 0.15
        + phone_score * 0.20
        + address_score * 0.05
    )
    return round(score, 2)


def calc_bonus(base_score: float, is_customer_matched: bool) -> float:
    if base_score >= 75 and is_customer_matched:
        return 3.0
    return 0.0


def calc_final_score(base_score: float, bonus: float) -> float:
    return round(min(100.0, base_score + bonus), 2)


def classify_company_match(final_score: float) -> str:
    if final_score >= 90:
        return "매칭"
    if final_score >= 80:
        return "검수필요"
    return "미매칭"


def classify_customer_match(is_matched: bool) -> str:
    return "일치" if is_matched else "불일치"
