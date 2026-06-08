import logging
import os
import threading
from typing import Any

from dingtalk_stream import AckMessage
import dingtalk_stream
from fastapi import FastAPI


BOT_TITLE = os.getenv("BOT_TITLE", "污水处理药剂价格早报")
DINGTALK_CLIENT_ID = os.getenv("DINGTALK_CLIENT_ID", "")
DINGTALK_CLIENT_SECRET = os.getenv("DINGTALK_CLIENT_SECRET", "")
_stream_thread_started = False
_stream_last_error = ""

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

logger = logging.getLogger("ding-post")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

app = FastAPI(title="DingTalk Wastewater Price Bot")


@app.on_event("startup")
def startup() -> None:
    start_stream_client_once()


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "streamConfigured": bool(DINGTALK_CLIENT_ID and DINGTALK_CLIENT_SECRET),
        "streamStarted": _stream_thread_started,
        "streamLastError": _stream_last_error,
    }


class PriceBotStreamHandler(dingtalk_stream.ChatbotHandler):
    def __init__(self, stream_logger: logging.Logger) -> None:
        super().__init__()
        self.logger = stream_logger

    async def process(
        self, callback: dingtalk_stream.CallbackMessage
    ) -> tuple[str, str]:
        incoming_message = dingtalk_stream.ChatbotMessage.from_dict(callback.data)
        self.logger.info("Received DingTalk bot message")
        self.reply_markdown(
            BOT_TITLE,
            render_price_markdown(MOCK_PRICE_JSON),
            incoming_message,
        )
        return AckMessage.STATUS_OK, "OK"


def start_stream_client_once() -> None:
    global _stream_thread_started

    if _stream_thread_started:
        return

    if not DINGTALK_CLIENT_ID or not DINGTALK_CLIENT_SECRET:
        logger.warning("DingTalk Stream credentials are not configured")
        return

    thread = threading.Thread(target=run_stream_client, daemon=True)
    thread.start()
    _stream_thread_started = True


def run_stream_client() -> None:
    global _stream_last_error

    logger.info("Starting DingTalk Stream client")
    try:
        credential = dingtalk_stream.Credential(
            DINGTALK_CLIENT_ID,
            DINGTALK_CLIENT_SECRET,
        )
        client = dingtalk_stream.DingTalkStreamClient(credential, logger=logger)
        client.register_callback_handler(
            dingtalk_stream.chatbot.ChatbotMessage.TOPIC,
            PriceBotStreamHandler(logger),
        )
        client.start_forever()
    except Exception as exc:
        _stream_last_error = str(exc)
        logger.exception("DingTalk Stream client stopped unexpectedly")


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
