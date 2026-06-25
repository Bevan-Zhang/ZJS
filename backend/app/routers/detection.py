"""检测结果接口：读取 results 目录下的 CSV，统计样本数/准确率，并提供逐样本与滚动流数据。"""
from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ..config import DATA_DIR

router = APIRouter(prefix="/api/detection", tags=["detection"])

RESULTS_DIR = DATA_DIR / "results"

COL_FILE = "文件名"
COL_TRUE = "真实攻击类型"
COL_PRED = "预测攻击类型"
COL_CONF = "Confidence"

RESULT_SAMPLE_CAP = 150   # 每个结果文件回传的逐样本条数上限（用于结果卡右侧滚动）
ROLL_CAP = 400            # 滚动流回传上限（前端循环滚动）


class Sample(BaseModel):
    name: str
    true: str
    pred: str
    correct: bool
    confidence: Optional[float] = None
    modality: Optional[str] = None


class FileStat(BaseModel):
    name: str
    total: int
    correct: int
    accuracy: float
    samples: list[Sample] = []


class DetectionResultOut(BaseModel):
    total: int
    correct: int
    accuracy: float
    file_count: int
    files: list[FileStat]


class RollOut(BaseModel):
    total: int
    rows: list[Sample]


def _read_text(path: Path) -> Optional[str]:
    for enc in ("utf-8-sig", "utf-8", "gbk", "gb18030"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return None


def _col_index(header: list[str], name: str) -> int:
    return header.index(name) if name in header else -1


def _modality_index(header: list[str]) -> int:
    for i, h in enumerate(header):
        if "模态" in h:
            return i
    return -1


def _to_float(s: str) -> Optional[float]:
    try:
        return round(float(s), 4)
    except (TypeError, ValueError):
        return None


def _parse(path: Path, sample_cap: int) -> tuple[int, int, list[Sample]]:
    """返回 (样本数, 命中数, 逐样本列表[:cap])。"""
    text = _read_text(path)
    if not text:
        return 0, 0, []
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return 0, 0, []
    header = [h.strip().lstrip("﻿") for h in rows[0]]
    ti, pi = _col_index(header, COL_TRUE), _col_index(header, COL_PRED)
    if ti < 0 or pi < 0:
        return 0, 0, []
    fi = _col_index(header, COL_FILE)
    ci = _col_index(header, COL_CONF)
    mi = _modality_index(header)

    total = correct = 0
    samples: list[Sample] = []
    for r in rows[1:]:
        if len(r) <= max(ti, pi):
            continue
        true_t, pred_t = r[ti].strip(), r[pi].strip()
        if not true_t and not pred_t:
            continue
        hit = true_t == pred_t
        total += 1
        if hit:
            correct += 1
        if len(samples) < sample_cap:
            samples.append(Sample(
                name=(r[fi].strip() if 0 <= fi < len(r) else f"#{total}"),
                true=true_t, pred=pred_t, correct=hit,
                confidence=_to_float(r[ci]) if 0 <= ci < len(r) else None,
                modality=(r[mi].strip() if 0 <= mi < len(r) else None),
            ))
    return total, correct, samples


@router.get("/results", response_model=DetectionResultOut)
def detection_results():
    files: list[FileStat] = []
    overall_total = overall_correct = 0
    if RESULTS_DIR.exists():
        for f in sorted(RESULTS_DIR.glob("*.csv")):
            if f.name.lower() == "roll.csv":
                continue  # roll 专供滚动流，不计入结果卡
            total, correct, samples = _parse(f, RESULT_SAMPLE_CAP)
            overall_total += total
            overall_correct += correct
            files.append(FileStat(
                name=f.name, total=total, correct=correct,
                accuracy=round(correct / total * 100, 2) if total else 0.0,
                samples=samples,
            ))
    acc = round(overall_correct / overall_total * 100, 2) if overall_total else 0.0
    return DetectionResultOut(
        total=overall_total, correct=overall_correct, accuracy=acc,
        file_count=len(files), files=files,
    )


@router.get("/roll", response_model=RollOut)
def detection_roll():
    """滚动流数据来源：results/roll.csv（含模态列）。"""
    path = RESULTS_DIR / "roll.csv"
    if not path.exists():
        return RollOut(total=0, rows=[])
    total, _correct, samples = _parse(path, ROLL_CAP)
    return RollOut(total=total, rows=samples)
