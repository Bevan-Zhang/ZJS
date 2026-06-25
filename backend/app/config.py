"""全局配置：从环境变量 + nodes.yaml 加载。"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    """运行时配置，全部可被环境变量覆盖（前缀无）。"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 数据库：默认 SQLite，控制面用不上重型 DB；要换 MySQL 直接改 DATABASE_URL
    # 放在 app/data（与 nodes.yaml 同目录，已挂载卷持久化）
    database_url: str = "sqlite:////app/app/data/control_plane.db"

    # SSH 默认凭据（nodes.yaml 里可逐节点覆盖）
    ssh_default_username: str = "root"
    ssh_default_password: Optional[str] = None
    ssh_default_key_path: Optional[str] = None
    ssh_connect_timeout: int = 10
    ssh_command_timeout: int = 600  # 单条命令最长执行时间（秒）

    # 节点注册表路径
    nodes_file: str = str(DATA_DIR / "nodes.yaml")

    # CORS（开发期前端 vite 直连用）
    cors_origins: str = "*"


class NodeCredential(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    key_path: Optional[str] = None


class NodeConfig(BaseModel):
    id: str
    name: str
    role: str = "netunit"          # netunit | host | server | controller
    ssh_host: Optional[str] = None  # 管理网 IP，用于 SSH
    ssh_port: int = 22
    direct_ip: Optional[str] = None  # controller 直连网卡对端 IP（备用通道）
    direct_iface: Optional[str] = None  # controller 侧网卡名
    username: Optional[str] = None
    password: Optional[str] = None
    key_path: Optional[str] = None
    enabled: bool = True

    def resolved_credential(self, settings: "Settings") -> NodeCredential:
        return NodeCredential(
            username=self.username or settings.ssh_default_username,
            password=self.password if self.password is not None else settings.ssh_default_password,
            key_path=self.key_path or settings.ssh_default_key_path,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_nodes() -> list[NodeConfig]:
    settings = get_settings()
    path = Path(settings.nodes_file)
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    nodes = raw.get("nodes", [])
    # 允许用环境变量注入逐节点密码：NODE_<ID大写>_PASSWORD
    result: list[NodeConfig] = []
    for item in nodes:
        node = NodeConfig(**item)
        env_pw = os.getenv(f"NODE_{node.id.upper()}_PASSWORD")
        if env_pw:
            node.password = env_pw
        result.append(node)
    return result


def get_node(node_id: str) -> Optional[NodeConfig]:
    for n in load_nodes():
        if n.id == node_id:
            return n
    return None


class Preset(BaseModel):
    """预设任务：把"在某网元跑某脚本"固化成一个按钮。"""

    id: str
    name: str
    node_id: str
    command: str                       # 如 python3 sender.py
    workdir: Optional[str] = None       # 如 /home/p4/njupt_traffic_sender
    venv: Optional[str] = None          # Python 虚拟环境目录，如 /home/p4/.virtualenvs/CENI（运行前 source 激活）
    sudo: bool = False                  # 是否需要 sudo
    stop_pattern: Optional[str] = None  # 结束运行时 pkill -f 的匹配串；留空则从 command 推断
    desc: Optional[str] = None


def load_presets() -> list[Preset]:
    path = DATA_DIR / "presets.yaml"
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [Preset(**item) for item in raw.get("presets", [])]


def get_preset(preset_id: str) -> Optional[Preset]:
    for p in load_presets():
        if p.id == preset_id:
            return p
    return None
