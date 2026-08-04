from app.market_discovery import _matches_test_automation, discovery_status


def test_market_discovery_matches_relevant_launches_without_overclaiming() -> None:
    assert _matches_test_automation("Acme QA", "AI-powered test automation")
    assert not _matches_test_automation("Acme Calendar", "Team scheduling")


def test_market_discovery_is_disabled_without_account_credentials(monkeypatch) -> None:
    monkeypatch.delenv("PRODUCT_HUNT_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("CRUNCHBASE_API_KEY", raising=False)
    status = discovery_status()
    assert status["product_hunt"]["enabled"] is False
    assert status["crunchbase"]["enabled"] is False
