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
2. 首版联调可以先不启用加签；如果启用“加签”，保存生成的 `secret`。
3. FC 部署完成后，将机器人回调地址配置为：

```text
https://你的FC域名/api/dingtalk/price-bot
```

4. 首次联调保持默认 `DINGTALK_ENABLE_SIGN_CHECK=false`，确认链路正常后再按需改为 `true`。
5. 在群里 @机器人或发送测试消息，预期返回“污水处理药剂价格早报” Markdown。

## 环境变量

| 变量 | 说明 |
| --- | --- |
| `PORT` | 服务端口，FC3 固定使用 `9000` |
| `BOT_TITLE` | Markdown 标题，默认“污水处理药剂价格早报” |
| `DINGTALK_BOT_SECRET` | 可选，启用钉钉加签校验时才需要 |
| `DINGTALK_ENABLE_SIGN_CHECK` | 可选，默认 `false` |

## GitHub Actions Secrets

在 GitHub 仓库 `Settings -> Secrets and variables -> Actions` 只需要先配置这 3 个必填项：

- `ALIBABA_CLOUD_ACCESS_KEY_ID`
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET`
- `ALIBABA_CLOUD_ACCOUNT_ID`
- `ALIBABA_CLOUD_REGION`

如果后续要启用钉钉加签校验，再额外配置：

- `DINGTALK_BOT_SECRET`
- `DINGTALK_ENABLE_SIGN_CHECK=true`

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

push 到 `main` 后，GitHub Actions 会执行语法检查和最小测试，通过后使用 Serverless Devs 基于 `s.yaml` 部署到 FC3。部署地域已固定为华东 1（杭州）：`cn-hangzhou`。
