from app.groq_rank import parse_rank_json


def test_parse_rank_json_strips_fence() -> None:
    raw = """```json
{"ranked_ids": ["a"], "items": [{"restaurant_id": "a", "explanation": "ok"}]}
```"""
    out = parse_rank_json(raw)
    assert out.ranked_ids == ["a"]
    assert out.items[0].explanation == "ok"
