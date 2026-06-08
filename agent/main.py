import base64
import hashlib
import hmac
import os
import time
from typing import Any
from urllib.parse import quote_plus, unquote_plus

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse


BOT_TITLE = os.getenv("BOT_TITLE", "污水处理药剂价格早报")
DINGTALK_BOT_SECRET = os.getenv("DINGTALK_BOT_SECRET", "")
DINGTALK_ENABLE_SIGN_CHECK = (
    os.getenv("DINGTALK_ENABLE_SIGN_CHECK", "false").lower() == "true"
)
SIGNATURE_MAX_AGE_SECONDS = 60 * 10

MOCK_PRICE_JSON: dict[str, Any] = {
    "updatedAt": "2026-06-08 08:30",
    "items": [
        {
            "name": "聚合氯化铝",
            "alias": "PAC",
            "spec": "含量 28%，喷雾型",
            "price": "1680-1850",
            "unit": "元/吨",
            "trend": "平稳",
            "change": "0%",
            "notes": "华东主流出厂参考价，按实际含量和运距浮动。",
        },
        {
            "name": "聚丙烯酰胺",
            "alias": "PAM",
            "spec": "阴离子，分子量 1200 万",
            "price": "9800-11800",
            "unit": "元/吨",
            "trend": "小幅上行",
            "change": "+1.5%",
            "notes": "高分子量型号询价增加，成交以订单为准。",
        },
        {
            "name": "复合碳源",
            "alias": "复合碳源",
            "spec": "COD 当量 20 万",
            "price": "900-1150",
            "unit": "元/吨",
            "trend": "平稳",
            "change": "0%",
            "notes": "园区污水厂补货节奏正常。",
        },
        {
            "name": "氢氧化钠",
            "alias": "片碱",
            "spec": "含量 99%",
            "price": "2850-3150",
            "unit": "元/吨",
            "trend": "偏弱",
            "change": "-0.8%",
            "notes": "下游按需采购，区域价差明显。",
        },
    ],
    "extras": {
        "sludgeDisposalPrice": {
            "title": "今日污泥处置参考价",
            "value": "280-420 元/吨",
            "notes": "含水率 80% 市政污泥，价格受地区、运输距离和处置方式影响。",
        },
        "morningBrief": [
            "水处理药剂市场整体以刚需采购为主，短期价格波动有限。",
            "部分地区环保检查趋严，污泥外运和处置成本需持续关注。",
            "建议采购报价时同步确认含量、包装、账期、运费和到货周期。",
        ],
    },
}

app = FastAPI(title="DingTalk Wastewater Price Bot")


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/api/dingtalk/price-bot")
async def dingtalk_price_bot(request: Request) -> JSONResponse:
    payload = await parse_json_payload(request)
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="request body must be a JSON object")

    if DINGTALK_ENABLE_SIGN_CHECK:
        verify_dingtalk_signature(request)

    return JSONResponse(build_markdown_response(MOCK_PRICE_JSON))


async def parse_json_payload(request: Request) -> Any:
    try:
        return await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid JSON request body") from exc


def verify_dingtalk_signature(request: Request) -> None:
    if not DINGTALK_BOT_SECRET:
        raise HTTPException(status_code=500, detail="DingTalk sign secret is not configured")

    timestamp = request.query_params.get("timestamp") or request.headers.get(
        "x-dingtalk-timestamp"
    )
    sign = request.query_params.get("sign") or request.headers.get("x-dingtalk-sign")
    if not timestamp or not sign:
        raise HTTPException(status_code=401, detail="missing DingTalk signature")

    try:
        timestamp_ms = int(timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="invalid DingTalk timestamp") from exc

    now_ms = int(time.time() * 1000)
    if abs(now_ms - timestamp_ms) > SIGNATURE_MAX_AGE_SECONDS * 1000:
        raise HTTPException(status_code=401, detail="expired DingTalk signature")

    expected = build_dingtalk_sign(timestamp, DINGTALK_BOT_SECRET)
    if not hmac.compare_digest(unquote_plus(sign), unquote_plus(expected)):
        raise HTTPException(status_code=401, detail="invalid DingTalk signature")


def build_dingtalk_sign(timestamp: str, secret: str) -> str:
    string_to_sign = f"{timestamp}\n{secret}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), string_to_sign, hashlib.sha256).digest()
    return quote_plus(base64.b64encode(digest).decode("utf-8"))


def build_markdown_response(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "msgtype": "markdown",
        "markdown": {
            "title": BOT_TITLE,
            "text": render_price_markdown(data),
        },
    }


def render_price_markdown(data: dict[str, Any]) -> str:
    lines = [
        f"### {BOT_TITLE}",
        "",
        f"> 更新时间：{data.get('updatedAt', '待更新')}",
        "",
        "| 品类 | 规格 | 价格 | 走势 |",
        "| --- | --- | --- | --- |",
    ]

    for item in data.get("items", []):
        price = f"{item['price']} {item['unit']}"
        trend = f"{item['trend']}（{item['change']}）"
        lines.append(f"| {item['alias']} | {item['spec']} | {price} | {trend} |")

    lines.extend(["", "#### 备注"])
    for item in data.get("items", []):
        lines.append(f"- {item['alias']}：{item['notes']}")

    extras = data.get("extras", {})
    sludge = extras.get("sludgeDisposalPrice", {})
    lines.extend(
        [
            "",
            f"#### {sludge.get('title', '今日污泥处置参考价')}",
            f"- {sludge.get('value', '待更新')}：{sludge.get('notes', '暂无说明')}",
            "",
            "#### 行业早报",
        ]
    )
    for brief in extras.get("morningBrief", []):
        lines.append(f"- {brief}")

    return "\n".join(lines)
