# 多模态网元控制面（Control Plane）

部署在 controller 节点的前后端分离管理后台：前端点按钮 → 后端经 **SSH(paramiko)** 把命令/脚本下发到指定网元 → 异步执行 → 前端轮询任务状态与输出。

## 架构

```
浏览器 ─65278─> nginx(frontend 容器) ──/api──> FastAPI(backend 容器:65279, host网络)
                                                   │ paramiko SSH
                          ┌────────────────────────┼────────────────────────┐
                       管理网 10.130.131.x      直连网卡 192.168.x.1↔.2
                          │                                                  │
                     网元1/3/4/7、host1、server1（直接跑 shell/python）
```

- **backend**：FastAPI + paramiko + SQLAlchemy(SQLite)。`network_mode: host`，确保能同时走管理网和 controller 直连网卡到达各节点。容器内用 python3.11，绕开 controller 仅有 python3.8 的限制。
- **frontend**：Vue3 + Vite + TS + Element Plus，构建为静态文件由 nginx 托管并反代 `/api`。
- **节点注册表**：`backend/app/data/nodes.yaml`，新增节点改这里即可。

## 部署（在 controller 上）

```bash
cp .env.example .env        # 填写 SSH 凭据
docker compose up -d --build
# 前端: http://10.130.131.239:65278/   后端文档: http://10.130.131.239:65279/docs
```

## 本地开发（Windows）

```powershell
# 后端
cd backend; pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000/docs
# 前端
cd frontend; npm install; npm run dev  # http://localhost:5173
```

## 主要接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/nodes` | 节点列表 |
| GET  | `/api/nodes/{id}/probe` | 实时探测 SSH 连通性 |
| POST | `/api/nodes/{id}/exec` | 下发 shell 命令（异步，返回 task） |
| POST | `/api/nodes/{id}/script` | 上传脚本并可选执行 |
| GET  | `/api/tasks/{id}` | 轮询任务状态/输出 |
| GET  | `/api/tasks` | 任务列表 |

## 待确认 / 待补

- ⚠️ 网元4 SSH IP 当前填 `10.130.31.51`，疑似应为 `10.130.131.51`，见 `nodes.yaml`。
- 网元 2/5/6/8/9、server2 暂无 SSH IP，已在 `nodes.yaml` 占位 `enabled: false`。
- 凭据：默认走 `.env` 的 `SSH_DEFAULT_*`；逐节点覆盖用 `NODE_<ID大写>_PASSWORD` 或 nodes.yaml 内 `password`/`key_path`。
