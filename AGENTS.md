# AGENTS.md — 多模态网络主动防御系统

> 给在不同机器上接手本项目的 AI/开发者。**动手改之前先读完本文件。** 它记录了架构、网络事实、约定和踩过的坑。

## 1. 这是什么

部署在 **controller 节点**的前后端分离管理后台 + 大屏。功能:展示多模态网络拓扑、对网元下发命令/脚本、加密恶意流量检测、溯源感知、内生安全主动防御。**无登录**。系统定位偏**展示 + 交互**:真正的攻击/检测/防御脚本多在命令行手动跑或经 SSH 触发,系统读结果来展示。

- 前端:Vue3 + Vite + TS + Element Plus + Vue Router + axios + echarts(`frontend/`)
- 后端:FastAPI + paramiko(SSH) + SQLAlchemy(SQLite) + httpx + PyYAML(`backend/`)
- 部署:controller 上 `docker compose up -d --build`(controller 只有 python3.8,一切跑在容器里)

## 2. ⚠️ 最重要的事实:数据面 ≠ 管理面

这是最容易踩的坑,改任何"连网元/发包/抓包"的东西前必须记住:

| | 用途 | 地址 | 谁能用 |
|---|---|---|---|
| **管理面** | controller SSH 控制、用户工作机访问 | `10.130.131.x`(SSH)、`192.168.x.2`(controller 直连网卡对端) | controller 走 **192.168.x.2 直连**;`10.130.131.x` 只有**用户工作机**能到 |
| **数据面** | 真实业务/攻击流量 | `100.0.0.x`(host1=100.0.0.100,server1=100.0.0.4) | 经 P4 多模态路径转发 |

- **controller 到不了 `10.130.131.x` 管理网**!所以 `backend/app/data/nodes.yaml` 里 SSH 的 `ssh_host` **全部用直连 IP `192.168.x.2`**,不是 `10.130.131.x`。(曾因用管理网 IP 导致 SSH `TimeoutError`。)
- 用户**工作机**能到 `10.130.131.x`,所以从工作机 `scp` 到各节点用 `10.130.131.x`。
- 后端容器用 `network_mode: host`,因此能同时走管理直连网卡和访问 controller 本机端口(如 8000)。

### 节点表(数据面/直连/管理 三套地址)

| 节点 | 数据面 | controller 直连(SSH 用) | 管理网(工作机 scp 用) | 备注 |
|---|---|---|---|---|
| host1 | ens7 / 100.0.0.100 / MAC fa:16:3e:05:03:55 | 192.168.10.2 | 10.130.131.240 | 流量源 |
| s1=网元1 | ens8(朝host1)/ens9(朝s3) | 192.168.1.2 | 10.130.131.254 | 收包/检测模型在此 |
| s3=网元3 | ens8(入) | 192.168.3.2 | 10.130.131.249 | |
| s4=网元4 | ens7(入) | 192.168.4.2 | 10.130.31.51 | 注意是 .31 不是 .131 |
| s7=网元7 | ens10(入) | 192.168.7.2 | 10.130.131.248 | |
| server1 | ens7 / 100.0.0.4 / MAC fa:16:3e:88:6f:30 | 192.168.11.2 | 10.130.131.216 | |
| controller | — | — | 10.130.131.239 | 后端/前端/optimize 栈在此 |

主路径:`host1 → s1 → s3 → s4 → s7 → server1`(全在数据面 y=300 直线)。SSH 用户/密码/sudo 全是 `p4`。

## 3. 跑起来 / 构建 / 部署

**端口**:前端 nginx **65278**、后端 uvicorn **65279**(controller 的 80 被宿主机自带 nginx 占了,所以不用 80)。

**本地开发**(任意机器):
```bash
cd frontend && npm install && npm run dev      # http://localhost:5173，/api 代理到 localhost:8000
cd backend  && pip install -r requirements.txt && uvicorn app.main:app --reload  # :8000/docs
```
**改完务必**:`cd frontend && npm run build`(`vue-tsc -b` 会类型检查,CI 级别拦错)。后端 `python -m py_compile app/**/*.py`。

**部署到 controller**(在用户工作机的 PowerShell):
```powershell
scp -r D:\WP\ZJS\backend\app  p4@10.130.131.239:~/ZJS/backend/
scp D:\WP\ZJS\backend\requirements.txt p4@10.130.131.239:~/ZJS/backend/
scp -r D:\WP\ZJS\frontend\src p4@10.130.131.239:~/ZJS/frontend/
scp D:\WP\ZJS\frontend\package.json p4@10.130.131.239:~/ZJS/frontend/
```
```bash
# controller 上
cd ~/ZJS && docker compose up -d --build      # 改了后端依赖/代码、前端代码时都要 --build
```
浏览器经 SSH 隧道访问:`ssh -L 65278:127.0.0.1:65278 p4@10.130.131.239` → `http://localhost:65278/`。

> **不要 `scp` 整个项目**(本地 `node_modules`/`dist` 是 Windows 产物,且巨大)。只传 `backend/app`、`frontend/src`、改动的配置文件。
> `backend/app/data/` 是**挂载卷**(`./backend/app/data:/app/app/data`):`nodes.yaml`/`presets.yaml`/`results/*.csv`/SQLite 改完**只需 `docker compose restart backend`,不用 rebuild**。但改后端**代码**或 `requirements.txt` 要 `--build`。

## 4. 目录与关键文件

```
backend/app/
  main.py                入口，注册所有 router
  config.py              Settings + nodes.yaml/presets.yaml 加载（Node/Preset 模型）
  ssh_manager.py         paramiko：run_command/run_streaming(流式)/upload/build_remote_command(组装 sudo+venv+行缓冲)
  services/executor.py   后台线程跑 SSH，把流式输出写回 DB（任务表）
  routers/
    nodes.py     /api/nodes：列表、探测(probe)、下发命令(exec 流式)、下发脚本
    presets.py   /api/presets：列表、run(可带 args)、stop(pkill)；预设来自 data/presets.yaml
    tasks.py     /api/tasks：轮询任务状态/输出
    detection.py /api/detection：results(每文件统计+逐样本) / roll(滚动流，读 results/roll.csv)
    trace.py     /api/trace：溯源感知，代理网元3 tactic-prediction（并行 agent 加的）
    defense.py   /api/defense：代理 controller_server_v2.py:8000（内生防御）
  data/
    nodes.yaml   节点注册表（ssh_host 用直连 IP！）
    presets.yaml 预设脚本（host1_sender / netunit1_listener / netunit1_main）
    results/     检测结果 CSV（roll.csv 给滚动流，其余给结果卡）+ README.txt

frontend/src/
  config/menu.ts         侧边栏结构（改这里增删页面，路由自动生成；MenuChild 有 presets/realRun/bindMain）
  router/index.ts        由 menu 生成路由；home/trace/defense 有专属视图映射，其余用 ModulePage
  api/client.ts          api / traceApi / defenseApi
  styles/theme.css       科技感深色主题 + 模态色板(.mod-ipv4/ipv6/mpls/geo/scion)+命中/误判(.vd-hit/miss)
  views/
    HomeView.vue         首页：只有 HomeTopo（网络拓扑）
    ModulePage.vue       通用功能页：有 presets→检测页布局；否则→DispatchPanel
    defense/             内生防御 4 页（MimicDetect/MimicAdaptive/MimicHoneypot/GameTheory）
    TraceOverview/Analysis/Graph.vue  溯源感知 3 页（并行 agent 加的）
  components/
    HomeTopo.vue         核心拓扑：2D/3D(CSS 伪3D 可拖拽缩放) + detection 模式(s1头上流量监听/检测图标+链路数据流动)
    RollTicker.vue       实时检测流（无缝循环滚动，高度对齐脚本控制台）
    SampleSpotlight.vue  逐样本聚光轮播
    DetectionResultPanel.vue 检测结果（每文件卡：3 tile + 聚光）
    ScriptRunnerCard.vue 单脚本控制台（真跑 SSH + 终端输出 + 参数输入框）
    PresetRunner.vue     渲染多个 ScriptRunnerCard
    ScriptButtons.vue    纯展示按钮（不跑代码，只切动效）
    DispatchPanel.vue    通用网元下发
    DefenseControl.vue   防御页状态灯+启停  RawJson.vue 接口原始返回折叠
  composables/useDashboard.ts  轮询 /api/defense/dashboard
  utils/detect.ts, utils/defense.ts  共用小工具

optimize/                底层 CENI 多VM P4 多模态网络的参考文档（9个md，只读参考，不是本系统代码）
内生安全防御接口文档.md   内生防御 4 页的数据源/接口（controller_server_v2.py:8000）
```

## 5. 功能模块现状

- **首页** `/home`:只有网络拓扑(2D/3D)。
- **加密恶意流量检测**:`变种威胁检测`(/traffic/variant,**已做实**:左模型检测控制台真跑 main.py+右实时检测流+拓扑联动+结果卡)、`未知攻击检测`(/traffic/unknown,展示态按钮)。
- **溯源感知**:检测总览/威胁链与意图分析/图谱解释(并行 agent 在做,接网元3)。
- **内生安全主动防御**:拟态入侵检测(s1)/拟态自适应防御(s4)/拟态蜜罐(s7)/博弈论选取——**已做页面+后端代理**,真实数据看 controller_server_v2 是否在跑;字段按文档 best-effort,每页有 RawJson 折叠核对真实返回。

## 6. 检测流水线(发包→收包→检测)

脚本在 `D:\WP\ZJS\sender\`(本地),实际跑在网元上:
- **发包** `sender_path.py`(host1 上 sudo 跑):把 `results`-rewrite 后的 pcap 重放到 ens7,**只发正向/或整条双向**,改 L2 MAC(host1↔server1),走数据面穿 P4 路径。`rewrite_pcaps_to_path.py` 负责把数据集 IP 改成 100.0.0.100↔100.0.0.4。
- **收包** `switch_listener.py`(各交换机上跑):tcpdump/scapy 抓 100.0.0.x 流,按 host1 发的 START/END UDP 控制包逐流切分存 pcap;**去重**(交换机把反向包弹回会产生重复帧,按 IP id+seq 去掉)。s1 抓双向(模型在 s1),s3/s4/s7 抓正向。
- **检测** `main.py`(网元1 venv `CENI` 里跑),分类结果写 CSV → controller 的 `backend/app/data/results/`。
- **要干净的双向流抓包**:数据面是活主机,server1 会真应答、host1 会回 RST,污染抓包。需 iptables 静音:server1 `iptables -A INPUT -i ens7 -s 100.0.0.100 -j DROP`、host1 `iptables -A OUTPUT -o ens7 -p tcp --tcp-flags RST RST -j DROP`(演示完撤掉)。反向那半来自**重放**(不是 server1),所以静音不会让它变单向。
- **路径模态**:演示固定 IPv4(`set_link_mode --all ipv4`),否则核心链路被 IPv6/MPLS/Geo 封装,中间交换机抓到的是外层头。

## 7. 约定 & 踩过的坑

- **SSH 一律走直连 IP `192.168.x.2`**(见 §2),不是管理网。
- **Element Plus 图标**已在 main.ts 全量注册,模板里用字符串名(如 `<component :is="'DataLine'"/>`)。
- **menu.ts 改一处即可**增删页面;`realRun=true` 的页用 PresetRunner 真跑+控制台,`bindMain=true` 所有动效绑模型检测运行。
- **Vue prop 布尔陷阱**:类型-only defineProps 里 `boolean` 缺省会被强制成 `false`(不是 undefined)。需要三态用字符串联合(如 `detection?: 'on'|'off'`)。
- **flexbox 滚动容器**:内部超长滚动内容会在 stretch 计算时撑爆父容器。解法:滚动轨道 `position:absolute`(见 RollTicker `.t-track`)。
- **后端流式输出**:`run_streaming` 逐块写库,前端轮询 `getTask` 看增长的 stdout;`sudo -S` 从 stdin 喂密码;`PYTHONUNBUFFERED=1 stdbuf -oL` 保证实时回显。
- **检测结果 CSV**:列 `文件名,真实攻击类型,(攻击手法),预测攻击类型,Confidence`;roll.csv 多一列**模态**。编码 utf-8-sig/gbk 都兼容。准确率=真实==预测。
- **预览/截图工具**:本项目拓扑含大量 SVG 辉光滤镜+动画,自带 preview_screenshot **经常超时**;改用 `preview_eval` 查 DOM 验证(读 class/文本/尺寸),比截图可靠。SPA 内 pushState 导航有时不换组件,验证时用 `location.href` 整页跳转。
- **可视化技能**:`~/.Codex/skills/frontend-design`(Anthropic 官方,做有辨识度的视觉)。本项目视觉方向已定:**青(#00e5ff)-深navy 控制台风**,改 UI 沿用,别另起灶。

## 8. 目录卫生

- `frontend/src/styles/` 只应有 `theme.css`。
- `backend/app/services/` 只应有 `__init__.py` 和 `executor.py`。
- 若哪天又冒出这两个目录里的 `App.vue`/`main.py`/`routers/` 等,那是 `scp -r`/`cp -r` 误拷进子目录的产物(没被任何 import 引用),删掉安全。务必只删副本,别碰上面两个真文件。

## 9. 改完自检清单

1. `cd frontend && npm run build`(类型检查必须过)。
2. `cd backend && python -m py_compile app/**/*.py`。
3. 涉及网元/SSH 的改动:确认用的是直连 IP。
4. 改了挂载数据(nodes/presets/results)→ `restart backend`;改了代码/依赖 → `--build`。
5. 部署后在浏览器(隧道 65278)实际点一遍受影响页面。
