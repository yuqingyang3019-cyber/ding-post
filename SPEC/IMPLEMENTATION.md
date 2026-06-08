# 最小实现与技术约束

## 最小实现

- 只实现钉钉 Stream 模式机器人消息接收与 Markdown 回复。
- 只保留 `/health` 作为 FC 健康检查和实例唤醒接口。
- 价格数据暂时使用 `MOCK_PRICE_JSON` 代码常量，不接入数据库、后台、采集任务或真实行情源。
- 不保留 HTTP 机器人回调接口，不实现 timestamp/sign 加签校验。
- 不引入合同业务、报价单上传、LLM 字段识别或钉盘上传。

## 技术选型

- Python 3.9，与 FC `custom.debian11` 自带 `python3` 运行环境保持一致。
- FastAPI：提供最小 HTTP 健康检查服务。
- `dingtalk-stream`：钉钉 Stream 模式官方 Python SDK，用于建立长连接、接收机器人消息、回复 Markdown。
- Uvicorn：FC3 自定义运行时 ASGI 启动器。
- Serverless Devs：基于 `s.yaml` 部署到阿里云 FC3。
- GitHub Actions：push 后执行语法检查和部署。

## SDK 版本策略

- `agent/requirements.txt` 不锁定版本，CI/CD 每次安装 Python 3.9 可解析的最新兼容版本。
- CI 使用 Python 3.9 执行 `python -m pip install -r agent/requirements.txt -t .python`，将运行依赖打包进 FC 自定义运行时代码包。
- GitHub Actions 使用当前主版本 action：
  - `actions/checkout@v4`
  - `actions/setup-python@v5`
  - `actions/setup-node@v4`
- Serverless Devs 使用 `npm install -g @serverless-devs/s` 安装最新发布版本。

## 验证策略

- 本地不要求运行测试。
- CI 不运行单元测试。
- CI 仅执行 `python -m py_compile agent/main.py`，确保首版代码语法可编译。
