from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_is_synthetic_demo() -> None:
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['mode'] == 'synthetic-demo'

def test_signals_return_evidence_status() -> None:
    response = client.get('/api/v1/signals')
    assert response.status_code == 200
    assert all(item['evidence_status'] for item in response.json())

def test_live_intelligence_has_citations_and_separates_inference() -> None:
    response = client.get('/api/v1/intelligence/today')
    assert response.status_code == 200
    payload = response.json()
    assert 'No newly verified' in payload['headline']
    assert all(signal['source_url'] and signal['fact'] for signal in payload['signals'])

def test_competitive_analysis_has_feature_leaders_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    from app import competitive_analysis
    from datetime import date
    monkeypatch.setattr(competitive_analysis, 'COMPETITOR_EVIDENCE', [{'vendor': 'UiPath', 'date': date.today().isoformat(), 'feature': 'Routing', 'detail': 'Routing', 'url': 'https://docs.uipath.com/'}])
    response = client.get('/api/v1/intelligence/competitive-analysis?range_days=30')
    assert response.status_code == 200
    payload = response.json()
    assert payload['mode'] == 'rule_based_fallback'
    assert payload['feature_leaders']
    assert payload['recommendations'] == []
    assert payload['fallback_reason'] == 'not_configured'
    assert all(item['vendors'] for item in payload['feature_leaders'])

def test_research_assistant_stream_returns_cited_evidence() -> None:
    response = client.post('/api/v1/ask/stream', json={'question': 'What has UiPath released?', 'period': '90', 'evidence_types': ['Official', 'Documentation'], 'competitors': []})
    assert response.status_code == 200
    assert 'event: complete' in response.text
    assert 'UiPath Agents release notes' in response.text

def test_automation_schedule_is_not_public() -> None:
    response = client.get('/api/v1/automation/schedule')
    assert response.status_code in {401, 503}


def test_owner_schedule_put_passes_cors_preflight() -> None:
    response = client.options('/api/v1/automation/schedule', headers={'Origin': 'https://kavitagurung.github.io', 'Access-Control-Request-Method': 'PUT', 'Access-Control-Request-Headers': 'authorization,content-type'})
    assert response.status_code == 200
    assert 'PUT' in response.headers['access-control-allow-methods']


def test_untrusted_origin_is_rejected() -> None:
    response = client.options('/api/v1/automation/schedule', headers={'Origin': 'https://untrusted.example', 'Access-Control-Request-Method': 'PUT'})
    assert response.status_code == 400
