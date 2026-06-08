from agent.main import health, render_price_markdown, MOCK_PRICE_JSON


def test_health() -> None:
    assert health() == {"ok": True}


def test_render_price_markdown_includes_extras() -> None:
    text = render_price_markdown(MOCK_PRICE_JSON)

    assert "PAC" in text
    assert "PAM" in text
    assert "复合碳源" in text
    assert "片碱" in text
    assert "今日污泥处置参考价" in text
    assert "行业早报" in text
