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
    response = client.get('/api/v1/intelligence/competitive-analysis?range_days=30')
    assert response.status_code == 200
    payload = response.json()
    assert payload['mode'] == 'rule_based_fallback'
    assert payload['feature_leaders']
    assert all(item['vendors'] for item in payload['feature_leaders'])
