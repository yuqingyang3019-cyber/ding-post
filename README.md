# ding-post

钉钉污水处理药剂价格早报机器人。服务部署在阿里云 FC3，通过钉钉 Stream 模式接收机器人消息并回复 Markdown 价格报表。

## 目录

```text
agent/
  main.py
  bootstrap.sh
  requirements.txt
SPEC/
  PRD.md
  ARCHITECTURE.md
  API.md
  IMPLEMENTATION.md
.github/
  workflows/
    deploy.yml
s.yaml
```

## 接口

- `GET /health`：健康检查和 FC 实例唤醒，返回 `{"ok": true}`。
- 机器人消息不走 HTTP 回调地址，改由钉钉 Stream 长连接接收。

## 钉钉 Stream 机器人配置

1. 在钉钉开放平台创建或进入企业内部应用。
2. 获取应用的 `Client ID` 和 `Client Secret`。旧版应用中通常对应 `AppKey` 和 `AppSecret`。
3. 在应用的机器人能力或消息推送配置中，启用机器人并将消息接收模式选择为 `Stream 模式`。
4. GitHub Actions 部署完成后，FC 会按 `s.yaml` 保持 1 个预留实例，用于维持 Stream 长连接。
5. 在群里 @机器人或发送测试消息，预期返回“污水处理药剂价格早报” Markdown。

## 环境变量

| 变量 | 说明 |
| --- | --- |
| `PORT` | 服务端口，FC3 固定使用 `9000` |
| `BOT_TITLE` | Markdown 标题，默认“污水处理药剂价格早报” |
| `DINGTALK_CLIENT_ID` | 钉钉应用 Client ID，旧版应用通常是 AppKey |
| `DINGTALK_CLIENT_SECRET` | 钉钉应用 Client Secret，旧版应用通常是 AppSecret |

## GitHub Actions Secrets

在 GitHub 仓库 `Settings -> Secrets and variables -> Actions` 配置这 5 个必填项：

- `ALIBABA_CLOUD_ACCESS_KEY_ID`
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET`
- `ALIBABA_CLOUD_ACCOUNT_ID`
- `DINGTALK_CLIENT_ID`
- `DINGTALK_CLIENT_SECRET`

建议使用 RAM 子账号 AccessKey，并限制到目标 FC3 资源，不要使用主账号密钥。

## 轻量验证

```bash
python -m py_compile agent/main.py
```

当前仓库不保留测试用例，CI 只做语法检查和部署。

## 部署

push 到 `main` 后，GitHub Actions 会执行语法检查，通过后使用 Serverless Devs 基于 `s.yaml` 部署到 FC3。部署地域已固定为华东 1（杭州）：`cn-hangzhou`。

Stream 模式依赖 WebSocket 长连接。`s.yaml` 已配置 `provisionConfig.defaultTarget=1` 和 `alwaysAllocateCPU=true`，部署后会持续保留 1 个实例并产生费用；不需要时请将 `defaultTarget` 改为 `0` 后重新部署。

## Stream 接入排查

如果钉钉提示“Stream模式接入失败”，先访问 FC 的 `/health` 唤醒实例并查看响应：

- `streamConfigured=false`：`DINGTALK_CLIENT_ID` 或 `DINGTALK_CLIENT_SECRET` 没有注入到 FC 环境变量。
- `streamStarted=false`：实例还没启动 Stream 线程，检查 FC 启动日志。
- `streamLastError` 非空：查看该错误和 FC 日志中的 `DingTalk Stream client stopped unexpectedly`。

如果 `/health` 正常但钉钉仍验证失败，优先确认 FC 预留实例配置已生效，因为 Stream 模式需要服务端长连接持续在线。
