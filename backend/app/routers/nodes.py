"""节点相关接口：列表、连通性探测、下发命令、下发脚本。"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import get_node, get_settings, load_nodes
from ..db import get_db
from ..models import Task, TaskKind, TaskStatus
from ..schemas import ExecRequest, NodeOut, ScriptRequest, TaskOut
from ..services.executor import run_script_task, run_stream_task
from ..ssh_manager import build_remote_command, probe

router = APIRouter(prefix="/api/nodes", tags=["nodes"])


@router.get("", response_model=list[NodeOut])
def list_nodes():
    """返回节点注册表（不做探测，快）。"""
    return [
        NodeOut(
            id=n.id, name=n.name, role=n.role, ssh_host=n.ssh_host,
            direct_ip=n.direct_ip, enabled=n.enabled,
        )
        for n in load_nodes()
    ]


@router.get("/{node_id}/probe", response_model=NodeOut)
def probe_node(node_id: str):
    """实时探测某节点 SSH 连通性。"""
    node = get_node(node_id)
    if node is None:
        raise HTTPException(404, f"未知节点 {node_id}")
    online, detail = probe(node, get_settings())
    return NodeOut(
        id=node.id, name=node.name, role=node.role, ssh_host=node.ssh_host,
        direct_ip=node.direct_ip, enabled=node.enabled, online=online, detail=detail,
    )


def _require_node(node_id: str):
    node = get_node(node_id)
    if node is None:
        raise HTTPException(404, f"未知节点 {node_id}")
    if not node.enabled:
        raise HTTPException(409, f"节点 {node_id} 未启用（缺少 SSH 配置）")
    return node


@router.post("/{node_id}/exec", response_model=TaskOut)
def exec_command(
    node_id: str,
    req: ExecRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """下发一条 shell 命令，异步执行，返回任务（pending）。"""
    node = _require_node(node_id)
    task = Task(node_id=node_id, kind=TaskKind.command, command=req.command, status=TaskStatus.pending)
    db.add(task)
    db.commit()
    db.refresh(task)
    remote = build_remote_command(req.command, workdir=None, sudo=False)
    background.add_task(run_stream_task, task.id, node, remote, None)
    return TaskOut.model_validate(task)


@router.post("/{node_id}/script", response_model=TaskOut)
def exec_script(
    node_id: str,
    req: ScriptRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """上传脚本内容到远端并可选执行。"""
    node = _require_node(node_id)
    remote_path = f"{req.remote_dir.rstrip('/')}/{req.filename}"
    label = req.run_cmd or f"upload-only -> {remote_path}"
    task = Task(node_id=node_id, kind=TaskKind.script, command=label, status=TaskStatus.pending)
    db.add(task)
    db.commit()
    db.refresh(task)
    content = req.content.encode("utf-8")
    background.add_task(run_script_task, task.id, node, content, remote_path, req.run_cmd)
    return TaskOut.model_validate(task)
