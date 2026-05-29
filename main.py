from __future__ import annotations

import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from config import (
    DEFAULT_COMPANY_REMOVE_WORDS,
    DEFAULT_SIDO_ALIAS,
    REQUIRED_COLUMNS,
    build_paths,
)
from excel_io import load_excel, save_excel, validate_required_columns
from matcher import match_dataframes


class DualLogger:
    def __init__(self, log_file: Path) -> None:
        self.log_file = log_file
        self.logger = logging.getLogger("excel_matcher")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()

        formatter = logging.Formatter("%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def info(self, message: str) -> None:
        self.logger.info(message)

    def error(self, message: str) -> None:
        self.logger.error(message)


def ensure_directories(paths) -> None:
    paths.input_dir.mkdir(parents=True, exist_ok=True)
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    paths.logs_dir.mkdir(parents=True, exist_ok=True)
    paths.rules_dir.mkdir(parents=True, exist_ok=True)


def load_json_mapping(path: Path, default_value: dict, file_label: str) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"규칙 파일이 없습니다: {path}\n"
            f"rules 폴더에 {file_label} 파일을 준비해 주세요."
        )
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"규칙 파일 JSON 형식이 올바르지 않습니다: {path}\n"
            f"오류 내용: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(f"규칙 파일은 JSON 객체 형식이어야 합니다: {path}")
    return data


def load_json_list(path: Path, default_value: List[str], file_label: str) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(
            f"규칙 파일이 없습니다: {path}\n"
            f"rules 폴더에 {file_label} 파일을 준비해 주세요."
        )
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"규칙 파일 JSON 형식이 올바르지 않습니다: {path}\n"
            f"오류 내용: {exc}"
        ) from exc

    if not isinstance(data, list):
        raise ValueError(f"규칙 파일은 JSON 배열 형식이어야 합니다: {path}")
    return [str(item) for item in data]


def validate_input_files(paths) -> None:
    if not paths.input_a_path.exists():
        raise FileNotFoundError(
            f"입력 파일 A.xlsx 를 찾을 수 없습니다.\n"
            f"경로: {paths.input_a_path}\n"
            f"input 폴더에 A.xlsx 파일을 넣어 주세요."
        )
    if not paths.input_b_path.exists():
        raise FileNotFoundError(
            f"입력 파일 B.xlsx 를 찾을 수 없습니다.\n"
            f"경로: {paths.input_b_path}\n"
            f"input 폴더에 B.xlsx 파일을 넣어 주세요."
        )


def progress_callback_factory(logger: DualLogger):
    last_percent = {"value": -1}

    def callback(current: int, total: int) -> None:
        if total <= 0:
            return
        percent = int(current * 100 / total)
        if percent != last_percent["value"]:
            last_percent["value"] = percent
            logger.info(f"진행률: {percent}% ({current}/{total})")

    return callback


def run() -> int:
    paths = build_paths()
    ensure_directories(paths)

    started_at = datetime.now()
    log_file = paths.logs_dir / f"run_{started_at.strftime('%Y%m%d_%H%M%S')}.log"
    logger = DualLogger(log_file)

    logger.info("엑셀 거래처/고객 매칭 프로그램을 시작합니다.")
    logger.info(f"실행 시작 시간: {started_at.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"입력 A 파일: {paths.input_a_path}")
    logger.info(f"입력 B 파일: {paths.input_b_path}")
    logger.info(f"출력 C 파일: {paths.output_c_path}")

    try:
        validate_input_files(paths)

        sido_alias = load_json_mapping(paths.sido_alias_path, DEFAULT_SIDO_ALIAS, "sido_alias.json")
        remove_words = load_json_list(
            paths.company_remove_words_path,
            DEFAULT_COMPANY_REMOVE_WORDS,
            "company_remove_words.json",
        )

        logger.info("입력 파일을 읽는 중입니다...")
        df_a = load_excel(paths.input_a_path)
        df_b = load_excel(paths.input_b_path)

        validate_required_columns(df_a, REQUIRED_COLUMNS, "A.xlsx")
        validate_required_columns(df_b, REQUIRED_COLUMNS, "B.xlsx")

        logger.info(f"A.xlsx 데이터 건수: {len(df_a)}")
        logger.info(f"B.xlsx 데이터 건수: {len(df_b)}")
        logger.info("매칭 작업을 시작합니다.")

        result_df = match_dataframes(
            df_a=df_a,
            df_b=df_b,
            remove_words=remove_words,
            sido_alias=sido_alias,
            progress_callback=progress_callback_factory(logger),
        )

        logger.info("결과 파일을 저장하는 중입니다...")
        try:
            save_excel(result_df, paths.output_c_path)
        except PermissionError as exc:
            raise PermissionError(
                "결과 파일 저장에 실패했습니다. output/C.xlsx 파일이 다른 프로그램(엑셀 등)에서 "
                "열려 있는지 확인한 뒤 닫고 다시 실행해 주세요."
            ) from exc
        except OSError as exc:
            raise OSError(
                f"결과 파일 저장 중 오류가 발생했습니다: {paths.output_c_path}\n"
                f"오류 내용: {exc}"
            ) from exc

        finished_at = datetime.now()
        logger.info(f"완료 시간: {finished_at.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"결과 파일 생성 완료: {paths.output_c_path}")
        logger.info(f"로그 파일: {log_file}")
        logger.info("프로그램 실행이 정상적으로 완료되었습니다.")
        return 0

    except FileNotFoundError as exc:
        logger.error(str(exc))
        return 1
    except ValueError as exc:
        logger.error(str(exc))
        return 1
    except Exception as exc:
        logger.error(f"예상하지 못한 오류가 발생했습니다: {exc}")
        logger.error(traceback.format_exc())
        return 1


def main() -> None:
    exit_code = run()
    print("\n종료하려면 아무 키나 누르세요...")
    try:
        input()
    except EOFError:
        pass
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
