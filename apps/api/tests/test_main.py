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
