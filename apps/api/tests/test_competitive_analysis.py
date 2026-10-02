from datetime import date, timedelta
import json
import httpx
import pytest
from app import competitive_analysis as analysis

@pytest.fixture(autouse=True)
def setup(monkeypatch):
    analysis._CACHE.clear()
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    monkeypatch.setenv('OPENAI_MODEL', 'configured-test-model')
    monkeypatch.setattr(analysis, 'COMPETITOR_EVIDENCE', [{'vendor': 'UiPath', 'date': date.today().isoformat(), 'feature': 'Routing', 'detail': 'Documented routing', 'url': 'https://docs.uipath.com/'}])

def mock_provider(monkeypatch, status=200, output=None, timeout=False):
    async def post(self, url, **kwargs):
        assert kwargs['json']['text']['format']['type'] == 'json_object'
        if timeout:
            raise httpx.ReadTimeout('timeout')
        return httpx.Response(status, request=httpx.Request('POST', url), json={'output_text': json.dumps(output)})
    monkeypatch.setattr(httpx.AsyncClient, 'post', post)

@pytest.mark.asyncio
async def test_empty_period_has_no_invented_trends(monkeypatch):
    analysis.COMPETITOR_EVIDENCE[0]['date'] = (date.today() - timedelta(days=60)).isoformat()
    result = await analysis.analyze_competitors(7)
    assert result['fallback_reason'] == 'no_evidence'
    assert result['themes'] == result['recommendations'] == result['feature_leaders'] == []

@pytest.mark.asyncio
async def test_future_evidence_is_excluded():
    analysis.COMPETITOR_EVIDENCE[0]['date'] = (date.today() + timedelta(days=1)).isoformat()
    assert (await analysis.analyze_competitors())['evidence'] == []

@pytest.mark.asyncio
@pytest.mark.parametrize('variable,reason', [('OPENAI_API_KEY', 'not_configured'), ('OPENAI_MODEL', 'model_not_configured')])
async def test_missing_configuration(monkeypatch, variable, reason):
    monkeypatch.delenv(variable)
    assert (await analysis.analyze_competitors())['fallback_reason'] == reason

@pytest.mark.asyncio
@pytest.mark.parametrize('status,reason', [(401, 'authentication_failed'), (403, 'access_denied'), (404, 'model_unavailable'), (429, 'rate_or_quota_limit'), (500, 'provider_error')])
async def test_provider_errors_have_safe_diagnostics(monkeypatch, status, reason, caplog):
    mock_provider(monkeypatch, status)
    assert (await analysis.analyze_competitors())['fallback_reason'] == reason
    assert reason in caplog.text and 'test-key' not in caplog.text

@pytest.mark.asyncio
async def test_timeout(monkeypatch):
    mock_provider(monkeypatch, timeout=True)
    assert (await analysis.analyze_competitors())['fallback_reason'] == 'provider_timeout'

@pytest.mark.asyncio
@pytest.mark.parametrize('output', [None, {'summary': 'x', 'themes': 'not a list', 'recommendations': []}, {'summary': 'x', 'themes': [], 'recommendations': [{'title': 'Idea', 'rationale': 'Evidence', 'market_fit_signal': 60, 'evidence_vendors': ['Invented vendor']}]}])
async def test_malformed_or_unsupported_output_is_rejected(monkeypatch, output):
    mock_provider(monkeypatch, output=output)
    assert (await analysis.analyze_competitors())['fallback_reason'] == 'invalid_response'

@pytest.mark.asyncio
async def test_success_cache_tracks_evidence_and_model(monkeypatch):
    mock_provider(monkeypatch, output={'summary': 'Documented routing', 'themes': [], 'recommendations': []})
    assert (await analysis.analyze_competitors())['mode'] == 'openai'
    mock_provider(monkeypatch, status=500)
    assert (await analysis.analyze_competitors())['mode'] == 'openai'
    monkeypatch.setenv('OPENAI_MODEL', 'different-model')
    assert (await analysis.analyze_competitors())['mode'] == 'rule_based_fallback'
