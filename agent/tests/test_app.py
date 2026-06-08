from fastapi.testclient import TestClient

from agent.main import app, render_price_markdown, MOCK_PRICE_JSON


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_price_bot_returns_markdown() -> None:
    response = client.post("/api/dingtalk/price-bot", json={"msgtype": "text"})

    assert response.status_code == 200
    body = response.json()
    assert body["msgtype"] == "markdown"
    assert body["markdown"]["title"] == "污水处理药剂价格早报"
    assert "PAC" in body["markdown"]["text"]
    assert "PAM" in body["markdown"]["text"]
    assert "复合碳源" in body["markdown"]["text"]
    assert "片碱" in body["markdown"]["text"]


def test_render_price_markdown_includes_extras() -> None:
    text = render_price_markdown(MOCK_PRICE_JSON)

    assert "今日污泥处置参考价" in text
    assert "行业早报" in text
