"""预设任务接口：列出按钮、一键运行（流式输出）。"""
from __future__ import annotations

import re
import shlex

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import Preset, get_node, get_settings, get_preset, load_presets
from ..db import get_db
from ..models import Task, TaskKind, TaskStatus
from ..schemas import TaskOut
from ..services.executor import run_stream_task
from ..ssh_manager import build_remote_command, run_streaming

router = APIRouter(prefix="/api/presets", tags=["presets"])


class PresetOut(BaseModel):
    id: str
    name: str
    node_id: str
    command: str
    workdir: str | None = None
    venv: str | None = None
    sudo: bool = False
    stop_pattern: str | None = None
    desc: str | None = None


def _kill_pattern(preset: Preset) -> str:
    """推断 pkill -f 的匹配串，并用字符类包住首字母避免 pkill 命中自身。"""
    base = preset.stop_pattern
    if not base:
        # 从 command 里取以 .py 结尾的脚本名，取不到则用整条 command
        tokens = [t for t in preset.command.split() if t.endswith(".py")]
        base = tokens[-1] if tokens else preset.command
    esc = re.escape(base)                 # 如 sender\.py
    return f"[{esc[0]}]{esc[1:]}"          # 如 [s]ender\.py（正则，且不匹配 pkill 自身命令行）


@router.get("", response_model=list[PresetOut])
def list_preset():
    return [PresetOut(**p.model_dump()) for p in load_presets()]


class RunArgs(BaseModel):
    args: str = ""  # 追加到命令后的可选参数，如 "--exp variant"


@router.post("/{preset_id}/run", response_model=TaskOut)
def run_preset(
    preset_id: str,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    body: RunArgs | None = None,
):
    preset = get_preset(preset_id)
    if preset is None:
        raise HTTPException(404, f"未知预设 {preset_id}")
    node = get_node(preset.node_id)
    if node is None or not node.enabled:
        raise HTTPException(409, f"预设目标节点 {preset.node_id} 不可用")

    extra = (body.args if body else "").strip()
    command = f"{preset.command} {extra}".strip() if extra else preset.command

    settings = get_settings()
    remote = build_remote_command(
        command, workdir=preset.workdir, sudo=preset.sudo, venv=preset.venv
    )
    sudo_pwd = node.resolved_credential(settings).password if preset.sudo else None

    display = f"[{preset.node_id}] {'sudo ' if preset.sudo else ''}{command}"
    if preset.workdir:
        display += f"  @ {preset.workdir}"

    task = Task(node_id=preset.node_id, kind=TaskKind.command, command=display, status=TaskStatus.pending)
    db.add(task)
    db.commit()
    db.refresh(task)
    background.add_task(run_stream_task, task.id, node, remote, sudo_pwd)
    return TaskOut.model_validate(task)


@router.post("/{preset_id}/stop")
def stop_preset(preset_id: str):
    """结束该预设在目标网元上正在运行的进程（pkill -f）。"""
    preset = get_preset(preset_id)
    if preset is None:
        raise HTTPException(404, f"未知预设 {preset_id}")
    node = get_node(preset.node_id)
    if node is None or not node.enabled:
        raise HTTPException(409, f"预设目标节点 {preset.node_id} 不可用")

    settings = get_settings()
    pattern = _kill_pattern(preset)
    cmd = f"pkill -f {shlex.quote(pattern)}"
    sudo_pwd = None
    if preset.sudo:
        cmd = f"sudo -S -p '' {cmd}"
        sudo_pwd = node.resolved_credential(settings).password
    try:
        code = run_streaming(node, settings, cmd, lambda _s: None, sudo_pwd)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"结束失败: {type(exc).__name__}: {exc}")
    # pkill: 0=已结束至少一个进程, 1=没有匹配进程
    return {"stopped": code == 0, "matched": code == 0}
