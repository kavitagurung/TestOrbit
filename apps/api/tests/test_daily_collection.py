from app.daily_collection import INITIAL_SOURCES

def test_initial_sources_are_public_and_competitor_scoped() -> None:
    assert {source['competitor'] for source in INITIAL_SOURCES} == {'UiPath', 'Opkey'}
    assert all(source['url'].startswith('https://') for source in INITIAL_SOURCES)
