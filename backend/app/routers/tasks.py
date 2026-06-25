"""任务查询接口：轮询状态/输出、列表。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Task
from ..schemas import TaskOut

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def list_tasks(
    node_id: str | None = Query(None),
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(Task).order_by(Task.id.desc()).limit(limit)
    if node_id:
        stmt = select(Task).where(Task.node_id == node_id).order_by(Task.id.desc()).limit(limit)
    return [TaskOut.model_validate(t) for t in db.scalars(stmt)]


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(404, f"任务 {task_id} 不存在")
    return TaskOut.model_validate(task)
