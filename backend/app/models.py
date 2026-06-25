"""ORM 模型：目前只需任务表，节点来自 nodes.yaml。"""
from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class TaskStatus(str, enum.Enum):
    pending = "pending"      # 已创建，未开始
    running = "running"      # SSH 执行中
    success = "success"      # exit_code == 0
    failed = "failed"        # exit_code != 0
    error = "error"          # 连接/传输等异常，未拿到 exit_code


class TaskKind(str, enum.Enum):
    command = "command"      # 直接执行 shell 命令
    script = "script"        # 上传脚本后执行


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    node_id: Mapped[str] = mapped_column(String(64), index=True)
    kind: Mapped[TaskKind] = mapped_column(Enum(TaskKind), default=TaskKind.command)
    command: Mapped[str] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.pending, index=True)

    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stdout: Mapped[str] = mapped_column(Text, default="")
    stderr: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
