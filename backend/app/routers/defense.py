"""内生安全主动防御：代理转发到 controller_server_v2.py（默认 127.0.0.1:8000）。

ZJS 后端是 host 网络，可直连 controller 本机的 8000；前端只连 ZJS(65279)，
统一从 /api/defense/* 走，避免前端跨域直连 8000。

Controller 不可达时，/dashboard 返回 mock 数据供前端 UI 调试。
"""
from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/defense", tags=["defense"])

# controller_server_v2.py 地址，可用环境变量覆盖
BASE = os.getenv("DEFENSE_API_BASE", "http://127.0.0.1:8000").rstrip("/")
TIMEOUT = float(os.getenv("DEFENSE_API_TIMEOUT", "15"))
START_TIMEOUT = float(os.getenv("DEFENSE_START_TIMEOUT", "660"))  # 启停操作超时
DASHBOARD_TIMEOUT = float(os.getenv("DEFENSE_DASHBOARD_TIMEOUT", "120"))  # dashboard 含 SSH 采集，首次较慢


def _get(path: str, timeout: float = TIMEOUT):
    try:
        r = httpx.get(f"{BASE}{path}", timeout=timeout)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, f"上游 {path} 返回 {e.response.status_code}")
    except Exception as e:  # noqa: BLE001  连不上视为 502
        raise HTTPException(502, f"controller_server_v2(8000) 不可达: {type(e).__name__}")


def _post(path: str, body: dict, timeout: float = TIMEOUT):
    try:
        r = httpx.post(f"{BASE}{path}", json=body, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, f"上游 {path} 返回 {e.response.status_code}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"controller_server_v2(8000) 不可达: {type(e).__name__}")


# ---- mock 数据（Controller 不可达时的兜底，供前端 UI 调试）----
def _mock_dashboard():
    return {
        "controller": "mock (offline)",
        "mimetic_status": {
            "mimetic_intrusion_detection": {"running": False, "status": "stopped"},
            "mimetic_adaptive_defense": {"running": False, "status": "stopped"},
            "mimetic_honeypot": {"running": False, "status": "stopped"},
        },
        # --- 拟态入侵检测 ---
        "intrusion": {
            "models": [
                {"id": 1, "name": "CNN", "desc": "卷积特征提取", "active": True},
                {"id": 2, "name": "GRU", "desc": "时序门控推理", "active": True},
                {"id": 3, "name": "DNN", "desc": "深度全连接",   "active": True},
                {"id": 4, "name": "MLP", "desc": "多层感知",     "active": False},
            ],
            "malicious_flows": [
                {"id": 1, "time": "14:32:07", "src": "10.0.4.51", "dst": "192.168.1.2", "type": "TLS 隧道",   "verdict": "恶意"},
                {"id": 2, "time": "14:32:11", "src": "10.0.4.88", "dst": "192.168.1.2", "type": "DNS 隐蔽",   "verdict": "恶意"},
                {"id": 3, "time": "14:32:18", "src": "10.0.5.12", "dst": "192.168.1.2", "type": "HTTP C2",    "verdict": "恶意"},
                {"id": 4, "time": "14:32:25", "src": "10.0.4.63", "dst": "192.168.1.2", "type": "ICMP 隧道",  "verdict": "恶意"},
                {"id": 5, "time": "14:32:31", "src": "10.0.6.7",  "dst": "192.168.1.2", "type": "SSH 异常",   "verdict": "恶意"},
                {"id": 6, "time": "14:32:39", "src": "10.0.4.51", "dst": "192.168.1.2", "type": "TLS 隧道",   "verdict": "恶意"},
                {"id": 7, "time": "14:32:44", "src": "10.0.5.99", "dst": "192.168.1.2", "type": "DNS 隐蔽",   "verdict": "恶意"},
                {"id": 8, "time": "14:32:50", "src": "10.0.4.17", "dst": "192.168.1.2", "type": "HTTP C2",    "verdict": "恶意"},
            ],
        },
        # --- 拟态自适应防御 ---
        "adaptive": {
            "executors": [
                {"id": 1, "name": "REMI-AIA",      "type": "optimized",   "online": True,  "desc": "免疫优化代理 (s4:8080)"},
                {"id": 2, "name": "Voting-5000",   "type": "traditional", "online": True,  "desc": "传统投票裁决器"},
                {"id": 3, "name": "hetero_ubuntu", "type": "traditional", "online": True,  "desc": "Ubuntu + Apache"},
                {"id": 4, "name": "hetero_centos", "type": "traditional", "online": True,  "desc": "CentOS + Nginx"},
                {"id": 5, "name": "hetero_debian", "type": "optimized",   "online": False, "desc": "Debian + Tomcat (REMI 优化后)"},
                {"id": 6, "name": "hetero_alpine", "type": "traditional", "online": True,  "desc": "Alpine + Lighttpd"},
                {"id": 7, "name": "hetero_fedora", "type": "optimized",   "online": True,  "desc": "Fedora + Caddy (REMI 优化后)"},
            ],
            "success_rate": 87.3,
            "rate_history": [82.4, 83.1, 79.8, 85.2, 86.7, 84.9, 87.3],
        },
        # --- 拟态蜜罐 ---
        "honeypot": {
            "trap_rate": 73.6,
            "attack_stats": [
                {"type": "SQL 注入",             "count": 47},
                {"type": "Apache CVE-2021-42013", "count": 35},
                {"type": "Nmap 扫描",            "count": 82},
                {"type": "目录扫描",             "count": 63},
                {"type": "XSS 跨站脚本",         "count": 28},
                {"type": "SSH 暴力破解",         "count": 41},
                {"type": "DNS 隧道",             "count": 19},
            ],
        },
        # ---- 博弈论（mock）----
        "latest_defense_plan": {
            "attack_type": "DDoS",
            "attacked_switches": [1, 3, 4, 7],
            "timestamp": 0,
            "assignments": {
                "1": {"strategy_name": "traffic_ctrl",     "display_name": "流量控制", "category": "traditional", "deploy_location": "网元1 (192.168.1.2)",  "utility": 0.643},
                "3": {"strategy_name": "rate_limit",      "display_name": "速率限制", "category": "traditional", "deploy_location": "网元3 (192.168.3.2)",  "utility": 0.639},
                "4": {"strategy_name": "load_balance",     "display_name": "负载均衡", "category": "traditional", "deploy_location": "网元4 (192.168.4.2)",  "utility": 0.623},
                "7": {"strategy_name": "mimetic_honeypot", "display_name": "拟态蜜罐", "category": "mimetic",     "deploy_location": "网元7 (192.168.7.2)",  "utility": 0.478},
            },
        },
        "attack_summary": {
            "1": {"is_under_attack": True,  "attack_type": "DDoS", "current_modal": "ipv4"},
            "3": {"is_under_attack": False, "attack_type": None,   "current_modal": "ipv6"},
            "4": {"is_under_attack": False, "attack_type": None,   "current_modal": "mpls"},
            "7": {"is_under_attack": False, "attack_type": None,   "current_modal": "scion"},
        },
    }


# ===== 总览 / 状态 =====
@router.get("/health")
def health():
    return _get("/health")


@router.get("/dashboard")
def dashboard():
    try:
        return _get("/defense/dashboard", timeout=DASHBOARD_TIMEOUT)
    except HTTPException:
        # Controller 不可达 → 返回 mock 数据供前端 UI 调试
        return JSONResponse(_mock_dashboard())


@router.get("/mimetic/status")
def mimetic_status():
    return _get("/mimetic/status")


@router.get("/status")
def net_status():
    return _get("/status")


# ===== 拟态启停 =====
@router.post("/mimetic/start")
async def mimetic_start(request: Request):
    return _post("/mimetic/start", await request.json(), timeout=START_TIMEOUT)


@router.post("/mimetic/stop")
async def mimetic_stop(request: Request):
    return _post("/mimetic/stop", await request.json(), timeout=START_TIMEOUT)


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
