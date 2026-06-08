# ding-post

钉钉污水处理药剂价格早报机器人。服务部署在阿里云 FC3，接收钉钉机器人回调并返回 Markdown 价格报表。

## 目录

```text
agent/
  main.py
  bootstrap.sh
  requirements.txt
  tests/
    test_app.py
SPEC/
  PRD.md
  ARCHITECTURE.md
  API.md
.github/
  workflows/
    deploy.yml
s.yaml
```

## 接口

- `GET /health`：健康检查，返回 `{"ok": true}`。
- `POST /api/dingtalk/price-bot`：钉钉机器人回调，返回 Markdown。

## 钉钉机器人配置

1. 在钉钉群中添加自定义机器人或企业内部机器人。
2. 安全设置建议选择“加签”，保存生成的 `secret`。
3. FC 部署完成后，将机器人回调地址配置为：

```text
https://你的FC域名/api/dingtalk/price-bot
```

4. 首次联调建议 `DINGTALK_ENABLE_SIGN_CHECK=false`，确认链路正常后再改为 `true`。
5. 在群里 @机器人或发送测试消息，预期返回“污水处理药剂价格早报” Markdown。

## 环境变量

| 变量 | 说明 |
| --- | --- |
| `PORT` | 服务端口，FC3 固定使用 `9000` |
| `BOT_TITLE` | Markdown 标题，默认“污水处理药剂价格早报” |
| `DINGTALK_BOT_SECRET` | 钉钉机器人加签密钥 |
| `DINGTALK_ENABLE_SIGN_CHECK` | 是否启用签名校验，首版建议先设为 `false` |
| `ALIBABA_CLOUD_REGION` | 阿里云 FC 地域，例如 `cn-hangzhou` |
| `FC_SERVICE_NAME` | 可选，FC 服务名 |
| `FC_FUNCTION_NAME` | 可选，FC 函数名 |

## GitHub Actions Secrets

在 GitHub 仓库 `Settings -> Secrets and variables -> Actions` 配置：

- `ALIBABA_CLOUD_ACCESS_KEY_ID`
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET`
- `ALIBABA_CLOUD_ACCOUNT_ID`
- `ALIBABA_CLOUD_REGION`
- `DINGTALK_BOT_SECRET`
- `DINGTALK_ENABLE_SIGN_CHECK`
- `FC_SERVICE_NAME`，可选
- `FC_FUNCTION_NAME`，可选

建议使用 RAM 子账号 AccessKey，并限制到目标 FC3 资源，不要使用主账号密钥。

## 轻量验证

```bash
python -m py_compile agent/main.py
```

如果本地已经安装测试依赖，可运行：

```bash
python -m pytest agent/tests
```

## 部署

push 到 `main` 后，GitHub Actions 会执行语法检查和最小测试，通过后使用 Serverless Devs 基于 `s.yaml` 部署到 FC3。
