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

