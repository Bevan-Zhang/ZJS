"""检测结果接口：读取 results 目录下的 CSV，统计样本数/准确率/分布，并提供逐样本与滚动流数据。

CSV 列：文件名, 模态, 真实攻击类型, 攻击手法, 预测攻击类型, 是否预测正确, Confidence
- 命中判定以「是否预测正确」列为准（预测词表与真实词表不一致，不能简单 true==pred）；
- 攻击类型分布 / 模态分布在后端按「全量行」聚合，避免前端只看截断样本而失真；
- 逐样本默认返回全部并打乱顺序（轮播立即覆盖各类型，不会卡在按文件名排序的 Benign 段）。
"""
from __future__ import annotations

import csv
import io
import random
from collections import defaultdict
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
COL_CORRECT = "是否预测正确"

ROLL_CAP = 300            # 滚动流回传上限（前端整列表 ×2 渲染做无缝循环，必须有界）


class Sample(BaseModel):
    name: str
    true: str
    pred: str
    correct: bool
    confidence: Optional[float] = None
    modality: Optional[str] = None


class TypeStat(BaseModel):
    type: str
    correct: int
    wrong: int


class ModalityStat(BaseModel):
    modality: str
    total: int
    correct: int


class FileStat(BaseModel):
    name: str
    total: int
    correct: int
    accuracy: float
    type_dist: list[TypeStat] = []
    modality_dist: list[ModalityStat] = []
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


def _is_correct(val: str, true_t: str, pred_t: str) -> bool:
    """命中判定：优先用「是否预测正确」列（值如 '✓ 正确' / '✗ 错误'），无该列时回退到 true==pred。"""
    v = val.strip()
    if v:
        if "正确" in v or v in ("1", "true", "True", "yes", "y", "Y", "✓"):
            return True
        if "错误" in v or v in ("0", "false", "False", "no", "n", "N", "✗"):
            return False
    return true_t == pred_t


def _parse(path: Path, sample_limit: int = 0) -> tuple[int, int, list[TypeStat], list[ModalityStat], list[Sample]]:
    """单遍扫描整文件，返回 (样本数, 命中数, 攻击类型分布, 模态分布, 逐样本[打乱, 截到 sample_limit])。"""
    text = _read_text(path)
    if not text:
        return 0, 0, [], [], []
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return 0, 0, [], [], []
    header = [h.strip().lstrip("﻿") for h in rows[0]]
    ti, pi = _col_index(header, COL_TRUE), _col_index(header, COL_PRED)
    if ti < 0 or pi < 0:
        return 0, 0, [], [], []
    fi = _col_index(header, COL_FILE)
    ci = _col_index(header, COL_CONF)
    mi = _modality_index(header)
    xi = _col_index(header, COL_CORRECT)

    total = correct = 0
    type_acc: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # type -> [correct, wrong]
    mod_acc: dict[str, list[int]] = defaultdict(lambda: [0, 0])   # modality -> [total, correct]
    samples: list[Sample] = []
    for r in rows[1:]:
        if len(r) <= max(ti, pi):
            continue
        true_t, pred_t = r[ti].strip(), r[pi].strip()
        if not true_t and not pred_t:
            continue
        corr_raw = r[xi].strip() if 0 <= xi < len(r) else ""
        hit = _is_correct(corr_raw, true_t, pred_t)
        total += 1
        if hit:
            correct += 1
        type_acc[true_t or "未知"][0 if hit else 1] += 1
        mod = (r[mi].strip() if 0 <= mi < len(r) else "") or "N/A"
        mod_acc[mod][0] += 1
        if hit:
            mod_acc[mod][1] += 1
        samples.append(Sample(
            name=(r[fi].strip() if 0 <= fi < len(r) else f"#{total}"),
            true=true_t, pred=pred_t, correct=hit,
            confidence=_to_float(r[ci]) if 0 <= ci < len(r) else None,
            modality=(r[mi].strip() if 0 <= mi < len(r) else None),
        ))

    # 打乱后再截断：轮播/滚动立即覆盖各攻击类型，而非按文件名排序卡在 Benign 段
    random.shuffle(samples)
    if sample_limit and sample_limit > 0:
        samples = samples[:sample_limit]

    type_dist = [
        TypeStat(type=k, correct=v[0], wrong=v[1])
        for k, v in sorted(type_acc.items(), key=lambda kv: -(kv[1][0] + kv[1][1]))
    ]
    mod_dist = [
        ModalityStat(modality=k, total=v[0], correct=v[1])
        for k, v in sorted(mod_acc.items(), key=lambda kv: -kv[1][0])
    ]
    return total, correct, type_dist, mod_dist, samples


@router.get("/results", response_model=DetectionResultOut)
def detection_results(file: Optional[str] = None, samples: int = 0):
    """检测结果。file 指定只取某个 CSV（如 results_variant.csv）；samples>0 时截断逐样本，默认 0=全部。"""
    files: list[FileStat] = []
    overall_total = overall_correct = 0
    if RESULTS_DIR.exists():
        for f in sorted(RESULTS_DIR.glob("*.csv")):
            if f.name.lower() == "roll.csv":
                continue  # roll 专供滚动流，不计入结果卡
            if file and f.name != file:
                continue  # 按页过滤到指定 CSV
            total, correct, type_dist, mod_dist, smp = _parse(f, samples)
            overall_total += total
            overall_correct += correct
            files.append(FileStat(
                name=f.name, total=total, correct=correct,
                accuracy=round(correct / total * 100, 2) if total else 0.0,
                type_dist=type_dist, modality_dist=mod_dist, samples=smp,
            ))
    acc = round(overall_correct / overall_total * 100, 2) if overall_total else 0.0
    return DetectionResultOut(
        total=overall_total, correct=overall_correct, accuracy=acc,
        file_count=len(files), files=files,
    )


@router.get("/roll", response_model=RollOut)
def detection_roll(limit: int = ROLL_CAP):
    """滚动流数据来源：results/roll.csv（含模态列）。打乱后截到 limit，保证各类型/模态都出现。"""
    path = RESULTS_DIR / "roll.csv"
    if not path.exists():
        return RollOut(total=0, rows=[])
    total, _correct, _td, _md, samples = _parse(path, limit)
    return RollOut(total=total, rows=samples)
