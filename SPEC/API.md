# API

## GET /health

健康检查和 FC 实例唤醒接口。

### 响应

```json
{
  "ok": true
}
```

## 钉钉 Stream 机器人消息

机器人消息不再通过 HTTP 回调地址进入服务。服务启动后使用 `dingtalk-stream` SDK 建立 WebSocket 长连接，注册机器人消息 topic，并在收到消息后回复 Markdown。

### 触发方式

在钉钉群中 @机器人或向机器人发送消息。

### 回复内容

```json
{
  "msgtype": "markdown",
  "markdown": {
    "title": "污水处理药剂价格早报",
    "text": "### 污水处理药剂价格早报\n..."
  }
}
```

### 必要配置

- `DINGTALK_CLIENT_ID`
- `DINGTALK_CLIENT_SECRET`

钉钉开放平台中需要将机器人消息接收模式配置为 `Stream 模式`。
