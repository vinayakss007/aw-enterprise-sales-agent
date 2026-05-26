"""Pure-function tests for the keyword retrieval helpers."""
from __future__ import annotations


def test_tokens_lowercase_and_drop_stopwords():
    from app.services.customer.knowledge_service import _tokens

    assert _tokens("The Quick Brown Fox") == ["quick", "brown", "fox"]
    # 1-char tokens are dropped, stopwords dropped.
    assert _tokens("a or b") == []


def test_tokens_split_on_punctuation():
    from app.services.customer.knowledge_service import _tokens

    assert _tokens("hello, world!") == ["hello", "world"]


def test_tokens_dedupe_preserving_first_occurrence_order():
    from app.services.customer.knowledge_service import _tokens

    assert _tokens("cat dog cat bird dog") == ["cat", "dog", "bird"]


def test_tokens_empty_or_whitespace():
    from app.services.customer.knowledge_service import _tokens

    assert _tokens("") == []
    assert _tokens("   \t\n") == []


def test_score_weights_title_more_than_content():
    """A title hit must outweigh a content-only hit on the same token."""
    from types import SimpleNamespace

    from app.services.customer.knowledge_service import _score

    title_hit = SimpleNamespace(
        title="Pricing", content="other stuff", tags=None, category=None
    )
    content_hit = SimpleNamespace(
        title="Onboarding", content="pricing info here", tags=None, category=None
    )
    assert _score(title_hit, ["pricing"]) > _score(content_hit, ["pricing"])


def test_score_adds_bonus_for_tag_match():
    from types import SimpleNamespace

    from app.services.customer.knowledge_service import _score

    tagged = SimpleNamespace(
        title="Onboarding", content="generic", tags=["pricing"], category=None
    )
    untagged = SimpleNamespace(
        title="Onboarding", content="generic", tags=None, category=None
    )
    assert _score(tagged, ["pricing"]) > _score(untagged, ["pricing"])
