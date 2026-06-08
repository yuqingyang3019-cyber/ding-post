# API

## GET /health

健康检查接口。

### 响应

```json
{
  "ok": true
}
```

## POST /api/dingtalk/price-bot

钉钉机器人回调接口。首版只要求请求体是 JSON 对象，后续可根据消息内容扩展关键词处理。

### 请求示例

```json
{
  "msgtype": "text",
  "text": {
    "content": "价格"
  }
}
```

### 响应示例

```json
{
  "msgtype": "markdown",
  "markdown": {
    "title": "污水处理药剂价格早报",
    "text": "### 污水处理药剂价格早报\n..."
  }
}
```

### 签名参数

当 `DINGTALK_ENABLE_SIGN_CHECK=true` 时，请求需要携带：

- `timestamp`：毫秒时间戳，可放在 query 参数或 `x-dingtalk-timestamp` 请求头。
- `sign`：钉钉加签值，可放在 query 参数或 `x-dingtalk-sign` 请求头。

签名使用 `timestamp + \"\\n\" + secret` 作为待签字符串，HMAC-SHA256 后 Base64 并 URL 编码。
