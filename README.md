ERP Demo — 管理 & 联调工具

包含用于本地开发和联调的小工具：

- `erp_service.py` — gRPC 服务实现（Initialization + Order）
- `sync_store.py` — SQLite 持久化（文件：`sync_results.db`）
- `show-sync-results.py` — CLI 表格打印最近的同步结果
- `admin_server.py` — Flask 管理界面（`/` 查看表格，`/api/sync-results` 返回 JSON，包含联调触发按钮）
- `sync_config.py` / `sync_runner.py` — 联调配置和脚本（读取环境变量或 sync_config.json）

数据库位置

`sync_results.db` 位于项目根（和 `erp_service.py` 同目录）。使用 `show-sync-results.py` 查看。

启动 admin 管理页面（开发）

    python admin_server.py

然后在浏览器打开 http://127.0.0.1:8080/ 查看表格并使用顶部的联调按钮（dry-run 默认）。

Docker 化（构建与运行）

项目包含 Dockerfile 和 docker-compose.yml，可将服务打包成镜像并用 docker-compose 启动：

构建镜像：

    docker build -t erp-demo:latest .

使用 docker-compose 启动（会把 sqlite 数据库文件挂载到宿主目录）:

    docker compose up --build -d

服务会暴露端口：
- gRPC: 50051
- admin UI: 8080

示例（不使用 docker-compose，直接运行镜像）：

    docker run -p 50051:50051 -p 8080:8080 -v $(pwd)/sync_results.db:/app/sync_results.db erp-demo:latest

注意：镜像内会用 `start.sh` 启动 `admin_server.py`（后台）并以 `erp_service.py` 作为前台进程。此模式适合开发演示；生产请用进程管理或把 admin 与 gRPC 服务拆分到不同容器。

使用国内镜像提前拉取依赖（可选但在部分网络受限环境强烈推荐）

1) 在构建镜像前，你可以先在宿主机把 requirements 中的依赖下载为 wheel 文件，使用清华镜像或阿里镜像：

PowerShell:

```powershell
cd C:\Users\yuj\Desktop\mmdh\mmapi\vv4\erp_demo
.
# 使用内置脚本（fetch_wheels.ps1），默认使用清华镜像
./fetch_wheels.ps1
```

Linux / macOS:

```bash
cd /path/to/erp_demo
./fetch_wheels.sh
```

这会在项目根生成 `./wheels/` 目录并下载对应的 whl 包。随后构建镜像时，Dockerfile 会把 `wheels/` 复制进镜像并优先使用本地 wheels 安装依赖（避免从 Docker Hub/PyPI 拉取）。

2) 然后构建镜像并启动（与之前相同）：

```powershell
docker compose up --build -d
```

如果你以后需要换镜像源，可以把脚本的第一个参数改为其他镜像地址，例如 `https://mirrors.aliyun.com/pypi/simple`。

依赖

依赖列在 `requirements.txt`，镜像构建会自动安装。常见依赖已包含：grpcio, protobuf, Flask, requests, tabulate

安全 & 生产建议

- admin 页面为开发工具，应仅在内网访问或加认证保护。
- 在生产环境下，建议将 admin 与 gRPC 服务拆分为独立容器并使用外部数据库或消息队列来做任务持久化。
ERP Demo — 管理 & 联调工具

包含用于本地开发和联调的小工具：

- `erp_service.py` — gRPC 服务实现（Initialization + Order）
- `sync_store.py` — SQLite 持久化（文件：`sync_results.db`）
- `show-sync-results.py` — CLI 表格打印最近的同步结果
- `admin_server.py` — Flask 管理界面（`/` 查看表格，`/api/sync-results` 返回 JSON，包含联调触发按钮）
- `sync_config.py` / `sync_runner.py` — 联调配置和脚本（读取环境变量或 sync_config.json）

数据库位置

`sync_results.db` 位于项目根（和 `erp_service.py` 同目录）。使用 `show-sync-results.py` 查看。

启动 admin 管理页面（默认 host 127.0.0.1 port 8080）

示例：

    C:/Users/yuj/AppData/Local/Microsoft/WindowsApps/python3.13.exe admin_server.py

然后在浏览器打开 http://127.0.0.1:8080/ 查看表格并使用顶部的联调按钮（dry-run 默认）。

sync_runner 用法示例：

    # 打印有效配置
    python sync_runner.py --show

    # 保存示例配置
    python sync_runner.py --save-sample

    # 构建并打印样例 Order 同步请求（dry-run）
    python sync_runner.py --call-order

    # 真正调用 Order 服务（需服务已运行）
    python sync_runner.py --call-order --no-dry-run --target localhost:50058

覆盖配置示例（PowerShell）：

    $env:SYNC_TOKEN_URL='https://open.handday.cn/grantauth/gettoken'
    $env:SYNC_CORP_ID='150046974'
    $env:SYNC_APP_ID='06e1014e6bfc11ee93b40c42a1db2810'
    $env:SYNC_APP_SECRET='262c405ee2d13482ea03ad7d83e9ebfee02d6584e4faa19aa172829569af2c3f'

注意：管理界面用于开发联调，请勿在生产环境中直接暴露。
# ERP Demo (gRPC)

This small demo contains a gRPC server and a client for checking ERP connection status.

Files:
- `erp_service.py` - minimal gRPC server implementation for `Initialization` service.
- `test_client.py` - client that calls `CheckErpConnection` with retry/backoff and logs.
- `start-server.ps1` - PowerShell script to start the server.
- `run-client.ps1` - PowerShell script to run the client.

Requirements:
- Python 3.8+ with `grpcio` and `protobuf` installed (your environment likely already has these).

How to run (PowerShell):

Start server (foreground):

```powershell
# from repository root
cd c:\Users\yuj\Desktop\mmdh\mmapi\vv4\erp_demo
# start server in the current terminal
python .\erp_service.py
```

Run client (in another terminal):

```powershell
cd c:\Users\yuj\Desktop\mmdh\mmapi\vv4\erp_demo
python .\test_client.py
```

Or using provided scripts:

```powershell
# start server (will block the terminal)
./start-server.ps1
# in another terminal, run client
./run-client.ps1
```

Start server in background (detached, logs written to files):

```powershell
./start-server-bg.ps1
Get-Content .\server.log -Wait  # follow the server log
```

Stop a background server started with the above script:

```powershell
./stop-server-bg.ps1
```

Custom host/port and target:

You can pass `--host` to `erp_service.py` to bind to a custom host:port, e.g.:

```powershell
python .\erp_service.py --host 0.0.0.0:50052
```

And the client can target a non-default host with the `--target` flag or `ERP_TARGET` env var:

```powershell
python .\test_client.py --target localhost:50052
# or
$env:ERP_TARGET = 'localhost:50052'; python .\test_client.py
```

Notes:
- If port 50051 is occupied, stop the process using it or edit `erp_service.py` to use another port.
- Pylance may report attribute access warnings on generated proto symbols that are created dynamically at runtime; these are benign if the runtime module works correctly.
