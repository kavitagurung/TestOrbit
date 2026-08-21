from app.market_discovery import _matches_test_automation, discovery_status, format_x_posts


def test_market_discovery_matches_relevant_launches_without_overclaiming() -> None:
    assert _matches_test_automation("Acme QA", "AI-powered test automation")
    assert not _matches_test_automation("Acme Calendar", "Team scheduling")


def test_market_discovery_is_disabled_without_account_credentials(monkeypatch) -> None:
    monkeypatch.delenv("PRODUCT_HUNT_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("CRUNCHBASE_API_KEY", raising=False)
    monkeypatch.delenv("X_BEARER_TOKEN", raising=False)
    status = discovery_status()
    assert status["product_hunt"]["enabled"] is False
    assert status["crunchbase"]["enabled"] is False
    assert status["x"]["enabled"] is False


def test_x_posts_are_source_linked_and_require_an_attributable_author() -> None:
    posts = format_x_posts({"data": [{"id": "123", "author_id": "u1", "text": "Playwright test automation", "created_at": "2026-08-21T09:00:00Z", "public_metrics": {"like_count": 4}}], "includes": {"users": [{"id": "u1", "username": "test_author"}]}})
    assert posts[0]["url"] == "https://x.com/test_author/status/123"
    assert posts[0]["likes"] == 4
