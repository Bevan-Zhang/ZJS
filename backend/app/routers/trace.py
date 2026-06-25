"""溯源感知接口：控制面后端经 SSH 代理到网元3 的 tactic-prediction 服务(127.0.0.1:8000)。

设计要点（见展示前端需求说明 / 演示脚本）：
- 不前端直连网元3，也不直连 Neo4j；前端只跟控制面 /api/trace/* 打交道。
- 复用 ssh_manager + nodes.yaml 的 netunit3 凭据，SSH 进网元3 跑 curl，解析 JSON 回吐。
- 网元3 没有 intent-graph 端点，这里用 /api/intent 的返回**就地合成**局部图谱。
- detect 触发沿用演示脚本的 manage_listener_bridge.sh（/api/detect 需 body，未知 schema）。
"""
from __future__ import annotations

import json
import re
import shlex
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..config import get_node, get_settings
from ..ssh_manager import run_command
from ..trace_batch import batch_threat_ids, filter_batch_threats

router = APIRouter(prefix="/api/trace", tags=["trace"])

# 分析服务所在网元（nodes.yaml 中的 id）与其本地监听地址
TACTIC_NODE_ID = "netunit3"
TACTIC_BASE = "http://127.0.0.1:8000"
# 演示脚本里触发检测的目录与脚本
BRIDGE_DIR = "/home/p4/test"
BRIDGE_SCRIPT = "manage_listener_bridge.sh"
BRIDGE_STATE = f"{BRIDGE_DIR}/bridge_submit_state.json"


def _node():
    node = get_node(TACTIC_NODE_ID)
    if node is None:
        raise HTTPException(500, f"未配置分析节点 {TACTIC_NODE_ID}")
    if not node.enabled:
        raise HTTPException(409, f"分析节点 {TACTIC_NODE_ID} 未启用")
    return node


def _ssh(command: str) -> str:
    """在网元3 上执行命令，返回 stdout（失败抛 502）。"""
    node = _node()
    settings = get_settings()
    try:
        res = run_command(node, settings, command)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"SSH 到 {TACTIC_NODE_ID} 失败: {type(exc).__name__}: {exc}")
    if res.exit_code != 0:
        detail = (res.stderr or res.stdout or "").strip()[:300]
        raise HTTPException(502, f"网元3 命令退出码 {res.exit_code}: {detail}")
    return res.stdout


def _curl_json(path: str) -> Any:
    """curl 网元3 的某个接口并解析 JSON。"""
    url = f"{TACTIC_BASE}{path}"
    out = _ssh(f"curl -s {shlex.quote(url)}")
    out = out.strip()
    if not out:
        raise HTTPException(502, f"网元3 接口 {path} 返回空")
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        raise HTTPException(502, f"网元3 接口 {path} 返回非 JSON: {out[:200]}")


# ============ 字段整形：把网元3 的原始结构压平成前端友好视图 ============

def _shape_threat(item: dict, stage_map: dict[str, str]) -> dict:
    p = item.get("props", {}) or {}
    tid = item.get("id", "")
    return {
        "threat_id": tid,
        "attack_type": p.get("resolved_attack_type") or p.get("ML_Class") or p.get("Predicted_Class"),
        "stage": p.get("stage") or stage_map.get(tid),
        "severity": p.get("resolved_severity") or p.get("Heuristic_Severity"),
        "ml_confidence": p.get("ML_Confidence"),
        "ml_class": p.get("ML_Class"),
        "predicted_category": p.get("Predicted_Category"),
        "modality": p.get("Primary_Modality") or p.get("True_Modal"),
        "file_name": p.get("File_Name"),
        "timestamp": p.get("timestamp") or item.get("time"),
        "stage_source": p.get("stage_source"),
        "stage_confidence": p.get("stage_confidence"),
        "stage_evidence": p.get("stage_evidence", []),
        "stage_scores": p.get("stage_scores", {}),
    }


def _shape_chain(item: dict) -> dict:
    p = item.get("props", {}) or {}
    stages = item.get("stages", []) or []
    confs = [s.get("confidence") for s in stages if isinstance(s.get("confidence"), (int, float))]
    return {
        "chain_id": item.get("chain_id"),
        "theme": p.get("theme"),
        "source": p.get("source"),
        "threat_id": p.get("threat_id"),
        "total_stages": p.get("total_stages", len(stages)),
        "confidence": max(confs) if confs else None,
        "stages": [
            {
                "stage": s.get("stage"),
                "order": s.get("order"),
                "confidence": s.get("confidence"),
                "desc": s.get("desc"),
                "modality": s.get("modality"),
                "capec_id": s.get("capec_id"),
            }
            for s in stages
        ],
    }


def _stage_map_from_chains(chains_raw: list[dict]) -> dict[str, str]:
    """从 chains 推每个 threat 的"当前阶段"：取 direct_escalation 链的首阶段。"""
    out: dict[str, str] = {}
    for c in chains_raw:
        p = c.get("props", {}) or {}
        tid = p.get("threat_id")
        if not tid or tid in out:
            continue
        if p.get("theme") == "direct_escalation":
            stages = c.get("stages", []) or []
            if stages:
                out[tid] = stages[0].get("stage")
    return out


# ============ 端点 ============

@router.get("/threats")
def list_threats(limit: int = Query(500, le=500)):
    """只返回 bridge 状态文件中记录的当前批次 threat。"""
    state_out = _ssh(f"cat {shlex.quote(BRIDGE_STATE)}").strip()
    if not state_out:
        raise HTTPException(502, "网元3批次状态文件为空")
    try:
        state = json.loads(state_out)
    except json.JSONDecodeError:
        raise HTTPException(502, "网元3批次状态文件不是有效 JSON")

    batch_ids = batch_threat_ids(state)
    if not batch_ids:
        return {"total": 0, "threats": []}

    threats_raw = _curl_json("/api/threats")
    chains_raw = _curl_json("/api/chains")
    items = threats_raw.get("threats", []) if isinstance(threats_raw, dict) else []
    chains = chains_raw.get("chains", []) if isinstance(chains_raw, dict) else []
    stage_map = _stage_map_from_chains(chains)
    selected = filter_batch_threats(items, batch_ids)
    shaped = [_shape_threat(t, stage_map) for t in selected]
    return {"total": len(shaped), "threats": shaped[:limit]}


@router.get("/chains")
def list_chains(threat_id: Optional[str] = Query(None)):
    """chain 列表，可按 threat_id 过滤。"""
    chains_raw = _curl_json("/api/chains")
    chains = chains_raw.get("chains", []) if isinstance(chains_raw, dict) else []
    shaped = [_shape_chain(c) for c in chains]
    if threat_id:
        shaped = [c for c in shaped if c.get("threat_id") == threat_id]
    return {"total": len(shaped), "chains": shaped}


@router.get("/intent/{threat_id}")
def get_intent(threat_id: str):
    """攻击意图（始终取完整 JSON：?json=1）。原样透传网元3 结构。"""
    data = _curl_json(f"/api/intent/{threat_id}?json=1")
    return data


def _norm_capec(cid: str) -> str:
    """归一 CAPEC 编号：CAPEC_469 / CAPEC-469 -> CAPEC-469。"""
    return (cid or "").replace("_", "-").strip()


@router.get("/intent-graph/{threat_id}")
def intent_graph(threat_id: str):
    """局部图谱：网元3 无此端点，用 /api/intent 的返回就地合成 nodes/edges。

    结构：threat -(当前阶段)-> stage; threat -(命中)-> CAPEC; CAPEC -> tactic/technique。
    """
    intent = _curl_json(f"/api/intent/{threat_id}?json=1")
    if not isinstance(intent, dict):
        raise HTTPException(502, "intent 返回结构异常")

    tid = intent.get("threat_id", threat_id)
    attack_type = intent.get("attack_type")
    modality = intent.get("modality")
    stage = intent.get("stage")
    intents = intent.get("intents") or intent.get("local_intents") or []

    nodes: list[dict] = [
        {"id": tid, "label": tid, "type": "threat", "attack_type": attack_type, "modality": modality}
    ]
    edges: list[dict] = []
    seen: set[str] = {tid}

    stage_id = None
    if stage:
        stage_id = f"stage::{stage}"
        if stage_id not in seen:
            nodes.append({"id": stage_id, "label": stage, "type": "stage"})
            seen.add(stage_id)
        edges.append({"source": tid, "target": stage_id, "label": "当前阶段"})

    capec_hit: list[str] = []
    for it in intents:
        cid = _norm_capec(it.get("attack_id", ""))
        if not cid:
            continue
        cap_node = f"capec::{cid}"
        if cap_node not in seen:
            nodes.append({
                "id": cap_node,
                "label": f"{cid} {it.get('attack_pattern', '')}".strip(),
                "type": "capec",
                "capec_id": cid,
                "attack_pattern": it.get("attack_pattern"),
                "severity": it.get("severity"),
                "matched_keywords": it.get("matched_keywords", []),
                "source": it.get("source"),
            })
            seen.add(cap_node)
            capec_hit.append(cid)
            edges.append({"source": tid, "target": cap_node, "label": "命中"})
            if stage_id:
                edges.append({"source": stage_id, "target": cap_node, "label": "可达"})
        for tac in it.get("tactics", []) or []:
            tac_node = f"tactic::{tac}"
            if tac_node not in seen:
                nodes.append({"id": tac_node, "label": tac, "type": "tactic"})
                seen.add(tac_node)
            edges.append({"source": cap_node, "target": tac_node, "label": "tactic"})
        for tech in it.get("techniques", []) or []:
            tech_node = f"technique::{tech}"
            if tech_node not in seen:
                nodes.append({"id": tech_node, "label": tech, "type": "technique"})
                seen.add(tech_node)
            edges.append({"source": cap_node, "target": tech_node, "label": "technique"})

    src = "local_subgraph"
    if intent.get("neo4j_intents"):
        src = "neo4j_kg"
    elif not intents:
        src = "rule_fallback"

    return {
        "threat_id": tid,
        "attack_type": attack_type,
        "modality": modality,
        "stage": stage,
        "capec_hit": capec_hit,
        "keywords": intent.get("keywords", []),
        "source": src,
        "nodes": nodes,
        "edges": edges,
    }


class DetectResult(BaseModel):
    threat_id: Optional[str] = None
    output: str


@router.post("/detect", response_model=DetectResult)
def trigger_detect():
    """触发一次本地 pcap+csv 直驱检测，返回最新 threat_id（沿用演示脚本的 bridge）。"""
    cmd = (
        f"cd {shlex.quote(BRIDGE_DIR)} && "
        f"bash {BRIDGE_SCRIPT} run-direct && bash {BRIDGE_SCRIPT} latest-threat"
    )
    out = _ssh(f"bash -lc {shlex.quote(cmd)}")
    m = re.search(r"threat_\d{8}_\d{6}", out)
    return DetectResult(threat_id=m.group(0) if m else None, output=out[-4000:])
