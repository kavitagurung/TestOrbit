from app.live_intelligence import daily_slack_brief


def test_daily_slack_brief_has_competitor_and_enterprise_sections() -> None:
    summary, citations = daily_slack_brief([])

    assert "Hi Kavita" in summary
    assert "New in test automation" in summary
    assert "UiPath" in summary
    assert "Opkey" in summary
    assert "Enterprise release watch" in summary
    assert "Workday" in summary
    assert "Coupa" in summary
    assert len(citations) == 4
