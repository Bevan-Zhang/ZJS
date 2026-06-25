"""内生安全主动防御：代理转发到 controller_server_v2.py（默认 127.0.0.1:8000）。

ZJS 后端是 host 网络，可直连 controller 本机的 8000；前端只连 ZJS(65279)，
统一从 /api/defense/* 走，避免前端跨域直连 8000。
"""
from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/defense", tags=["defense"])

# controller_server_v2.py 地址，可用环境变量覆盖
BASE = os.getenv("DEFENSE_API_BASE", "http://127.0.0.1:8000").rstrip("/")
TIMEOUT = float(os.getenv("DEFENSE_API_TIMEOUT", "8"))


def _get(path: str):
    try:
        r = httpx.get(f"{BASE}{path}", timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, f"上游 {path} 返回 {e.response.status_code}")
    except Exception as e:  # noqa: BLE001  连不上视为 502
        raise HTTPException(502, f"controller_server_v2(8000) 不可达: {type(e).__name__}")


def _post(path: str, body: dict):
    try:
        r = httpx.post(f"{BASE}{path}", json=body, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, f"上游 {path} 返回 {e.response.status_code}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"controller_server_v2(8000) 不可达: {type(e).__name__}")


# ===== 总览 / 状态 =====
@router.get("/health")
def health():
    return _get("/health")


@router.get("/dashboard")
def dashboard():
    return _get("/defense/dashboard")


@router.get("/mimetic/status")
def mimetic_status():
    return _get("/mimetic/status")


@router.get("/status")
def net_status():
    return _get("/status")


# ===== 拟态启停 =====
@router.post("/mimetic/start")
async def mimetic_start(request: Request):
    return _post("/mimetic/start", await request.json())


@router.post("/mimetic/stop")
async def mimetic_stop(request: Request):
    return _post("/mimetic/stop", await request.json())


@router.post("/mimetic/stop-all")
def mimetic_stop_all():
    return _post("/mimetic/stop-all", {})


# ===== 博弈论 =====
@router.post("/game-theory/optimal-strategy")
async def game_optimal(request: Request):
    return _post("/game-theory/optimal-strategy", await request.json())


@router.post("/game-theory/apply-optimal")
async def game_apply(request: Request):
    return _post("/game-theory/apply-optimal", await request.json())


@router.post("/game-theory/combination")
def game_combination():
    return _post("/game-theory/combination", {})
