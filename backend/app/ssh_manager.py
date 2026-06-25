"""paramiko SSH 封装：执行命令 / 上传文件 / 探测连通性。"""
from __future__ import annotations

import io
import time
from dataclasses import dataclass
from typing import Callable, Optional

import paramiko

from .config import NodeConfig, Settings


@dataclass
class ExecResult:
    exit_code: int
    stdout: str
    stderr: str


def _build_client(node: NodeConfig, settings: Settings) -> paramiko.SSHClient:
    if not node.ssh_host:
        raise ValueError(f"节点 {node.id} 未配置 ssh_host，无法连接")
    cred = node.resolved_credential(settings)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    pkey = None
    if cred.key_path:
        pkey = paramiko.RSAKey.from_private_key_file(cred.key_path)

    client.connect(
        hostname=node.ssh_host,
        port=node.ssh_port,
        username=cred.username,
        password=cred.password,
        pkey=pkey,
        timeout=settings.ssh_connect_timeout,
        banner_timeout=settings.ssh_connect_timeout,
        auth_timeout=settings.ssh_connect_timeout,
        allow_agent=False,
        look_for_keys=False,
    )
    return client


def run_command(node: NodeConfig, settings: Settings, command: str) -> ExecResult:
    """在节点上同步执行一条命令，返回退出码与输出。"""
    client = _build_client(node, settings)
    try:
        stdin, stdout, stderr = client.exec_command(command, timeout=settings.ssh_command_timeout)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        code = stdout.channel.recv_exit_status()
        return ExecResult(exit_code=code, stdout=out, stderr=err)
    finally:
        client.close()


def upload_and_run(
    node: NodeConfig,
    settings: Settings,
    content: bytes,
    remote_path: str,
    run_cmd: Optional[str] = None,
) -> ExecResult:
    """上传脚本/代码到远端路径，可选执行。run_cmd 为空则只传不跑。"""
    client = _build_client(node, settings)
    try:
        sftp = client.open_sftp()
        try:
            sftp.putfo(io.BytesIO(content), remote_path)
            sftp.chmod(remote_path, 0o755)
        finally:
            sftp.close()
        if not run_cmd:
            return ExecResult(exit_code=0, stdout=f"已上传至 {remote_path}", stderr="")
        stdin, stdout, stderr = client.exec_command(run_cmd, timeout=settings.ssh_command_timeout)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        code = stdout.channel.recv_exit_status()
        return ExecResult(exit_code=code, stdout=out, stderr=err)
    finally:
        client.close()


def upload_file(node: NodeConfig, settings: Settings, content: bytes, remote_path: str) -> None:
    """仅上传文件（供脚本下发先传后跑）。"""
    client = _build_client(node, settings)
    try:
        sftp = client.open_sftp()
        try:
            sftp.putfo(io.BytesIO(content), remote_path)
            sftp.chmod(remote_path, 0o755)
        finally:
            sftp.close()
    finally:
        client.close()


def run_streaming(
    node: NodeConfig,
    settings: Settings,
    command: str,
    on_chunk: Callable[[str], None],
    sudo_password: Optional[str] = None,
) -> int:
    """流式执行：逐块把 stdout/stderr 通过 on_chunk 回吐，返回退出码。

    sudo_password 不为空时，把密码 + EOF 写入 stdin（供 `sudo -S` 读取）。
    对不读 stdin 的程序无副作用。
    """
    client = _build_client(node, settings)
    try:
        transport = client.get_transport()
        assert transport is not None
        chan = transport.open_session()
        chan.exec_command(command)

        if sudo_password is not None:
            try:
                chan.sendall((sudo_password + "\n").encode())
                chan.shutdown_write()
            except Exception:  # noqa: BLE001
                pass

        while True:
            got = False
            while chan.recv_ready():
                data = chan.recv(8192)
                if data:
                    on_chunk(data.decode("utf-8", errors="replace"))
                    got = True
            while chan.recv_stderr_ready():
                data = chan.recv_stderr(8192)
                if data:
                    on_chunk(data.decode("utf-8", errors="replace"))
                    got = True
            if chan.exit_status_ready() and not chan.recv_ready() and not chan.recv_stderr_ready():
                break
            if not got:
                time.sleep(0.15)

        return chan.recv_exit_status()
    finally:
        client.close()


def build_remote_command(
    command: str, workdir: Optional[str], sudo: bool, venv: Optional[str] = None
) -> str:
    """组装最终远端命令：可选 source 虚拟环境 + cd 目录 + 强制行缓冲(实时回显) + 合并 stderr + 可选 sudo -S。

    venv 给定时先 `source <venv>/bin/activate`（用绝对路径，sudo 以 root 运行也能正确指向该 venv）。
    PYTHONUNBUFFERED=1 让 Python 立即吐出每行（否则管道下块缓冲，进度会卡到最后才出现）；
    stdbuf -oL -eL 对一般 C 程序同样强制行缓冲（Ubuntu coreutils 自带）。
    """
    import shlex

    parts = ""
    if venv:
        parts += f"source {shlex.quote(venv + '/bin/activate')} && "
    if workdir:
        parts += f"cd {shlex.quote(workdir)} && "
    parts += f"PYTHONUNBUFFERED=1 stdbuf -oL -eL {command} 2>&1"
    wrapped = f"bash -c {shlex.quote(parts)}"
    if sudo:
        # -S 从 stdin 读密码，-p '' 去掉提示语
        return f"sudo -S -p '' {wrapped}"
    return wrapped


def probe(node: NodeConfig, settings: Settings) -> tuple[bool, str]:
    """探测节点可达性：返回 (是否在线, 说明)。"""
    if not node.enabled:
        return False, "disabled"
    if not node.ssh_host:
        return False, "no ssh_host"
    try:
        res = run_command(node, settings, "echo ok")
        if res.exit_code == 0:
            return True, "online"
        return False, f"exit={res.exit_code}"
    except Exception as exc:  # noqa: BLE001  探测失败即视为离线
        return False, type(exc).__name__ + ": " + str(exc)
