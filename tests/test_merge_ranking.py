"""Pure merge / grounding tests (no Groq)."""

from app.llm_types import LLMRankItem, LLMRankResponse
from app.merge_ranking import merge_ranked_with_pool
from app.records import RestaurantRecord
from app.schemas import BudgetBand


def _rec(rid: str, name: str, rating: float) -> RestaurantRecord:
    return RestaurantRecord(
        restaurant_id=rid,
        name=name,
        location="Loc",
        cuisine="Chinese",
        rating=rating,
        cost_band=BudgetBand.medium,
        url=None,
    )


def test_merge_respects_llm_order_and_grounds() -> None:
    pool = [_rec("a", "A", 4.0), _rec("b", "B", 4.5), _rec("c", "C", 3.0)]
    parsed = LLMRankResponse(
        ranked_ids=["c", "ghost", "b"],
        items=[
            LLMRankItem(restaurant_id="c", explanation="Why c"),
            LLMRankItem(restaurant_id="b", explanation="Why b"),
        ],
    )
    out = merge_ranked_with_pool(
        pool,
        parsed,
        top_n=3,
        fallback_explanation="fb",
    )
    assert [r.restaurant_id for r in out] == ["c", "b", "a"]
    assert out[0].explanation == "Why c"
    assert out[1].explanation == "Why b"
    assert out[2].explanation == "fb"


def test_unknown_ids_only_use_pool_order() -> None:
    pool = [_rec("x", "X", 5.0), _rec("y", "Y", 4.0)]
    parsed = LLMRankResponse(ranked_ids=["nope"], items=[])
    out = merge_ranked_with_pool(pool, parsed, top_n=2, fallback_explanation="fb")
    assert [r.restaurant_id for r in out] == ["x", "y"]
