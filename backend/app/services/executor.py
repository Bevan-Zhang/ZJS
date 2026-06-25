"""任务执行：在后台线程跑 SSH，**流式**把输出写回 DB（前端轮询即可看到实时进度）。"""
from __future__ import annotations

import datetime as dt
import time
from typing import Optional

from ..config import NodeConfig, get_settings
from ..db import SessionLocal
from ..models import Task, TaskStatus
from ..ssh_manager import run_streaming, upload_file


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def run_stream_task(
    task_id: int,
    node: NodeConfig,
    remote_command: str,
    sudo_password: Optional[str] = None,
) -> None:
    """流式执行一条远端命令。remote_command 为已组装好的最终命令。"""
    settings = get_settings()
    db = SessionLocal()
    try:
        task = db.get(Task, task_id)
        if task is None:
            return
        task.status = TaskStatus.running
        task.started_at = _utcnow()
        task.stdout = ""
        db.commit()

        last_commit = time.monotonic()

        def on_chunk(text: str) -> None:
            nonlocal last_commit
            task.stdout = (task.stdout or "") + text
            now = time.monotonic()
            if now - last_commit > 0.3:   # 限流提交，避免过于频繁写库
                db.commit()
                last_commit = now

        try:
            code = run_streaming(node, settings, remote_command, on_chunk, sudo_password)
            task.exit_code = code
            task.status = TaskStatus.success if code == 0 else TaskStatus.failed
        except Exception as exc:  # noqa: BLE001
            task.status = TaskStatus.error
            task.error = f"{type(exc).__name__}: {exc}"
        finally:
            task.finished_at = _utcnow()
            db.commit()
    finally:
        db.close()


def run_script_task(
    task_id: int,
    node: NodeConfig,
    content: bytes,
    remote_path: str,
    run_cmd: Optional[str],
) -> None:
    """先 SFTP 上传脚本，再（可选）流式执行。"""
    settings = get_settings()
    db = SessionLocal()
    try:
        task = db.get(Task, task_id)
        if task is None:
            return
        task.status = TaskStatus.running
        task.started_at = _utcnow()
        task.stdout = ""
        db.commit()
        try:
            upload_file(node, settings, content, remote_path)
            task.stdout = f"[已上传] {remote_path}\n"
            db.commit()
            if run_cmd:
                last_commit = time.monotonic()

                def on_chunk(text: str) -> None:
                    nonlocal last_commit
                    task.stdout = (task.stdout or "") + text
                    now = time.monotonic()
                    if now - last_commit > 0.3:
                        db.commit()
                        last_commit = now

                code = run_streaming(node, settings, f"bash -c '{run_cmd} 2>&1'", on_chunk)
                task.exit_code = code
                task.status = TaskStatus.success if code == 0 else TaskStatus.failed
            else:
                task.exit_code = 0
                task.status = TaskStatus.success
        except Exception as exc:  # noqa: BLE001
            task.status = TaskStatus.error
            task.error = f"{type(exc).__name__}: {exc}"
        finally:
            task.finished_at = _utcnow()
            db.commit()
    finally:
        db.close()
