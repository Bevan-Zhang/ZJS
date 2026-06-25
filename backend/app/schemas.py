"""Pydantic 出入参模型。"""
from __future__ import annotations

import datetime as dt
from typing import Optional

from pydantic import BaseModel

from .models import TaskKind, TaskStatus


class NodeOut(BaseModel):
    id: str
    name: str
    role: str
    ssh_host: Optional[str] = None
    direct_ip: Optional[str] = None
    enabled: bool
    online: Optional[bool] = None       # 仅在带探测的接口里返回
    detail: Optional[str] = None


class ExecRequest(BaseModel):
    command: str


class ScriptRequest(BaseModel):
    filename: str                       # 远端文件名，如 collect.py
    content: str                        # 脚本文本内容
    remote_dir: str = "/tmp"
    run_cmd: Optional[str] = None       # 如 "python3 /tmp/collect.py"，留空则只上传


class TaskOut(BaseModel):
    id: int
    node_id: str
    kind: TaskKind
    command: str
    status: TaskStatus
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    created_at: Optional[dt.datetime] = None
    started_at: Optional[dt.datetime] = None
    finished_at: Optional[dt.datetime] = None

    model_config = {"from_attributes": True}
