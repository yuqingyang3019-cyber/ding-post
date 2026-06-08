from fastapi.testclient import TestClient

from agent.main import app, render_price_markdown, MOCK_PRICE_JSON


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_render_price_markdown_includes_extras() -> None:
    text = render_price_markdown(MOCK_PRICE_JSON)

    assert "PAC" in text
    assert "PAM" in text
    assert "复合碳源" in text
    assert "片碱" in text
    assert "今日污泥处置参考价" in text
    assert "行业早报" in text
