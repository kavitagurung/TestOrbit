from app.intelligence import (classify_claim, evidence_status, importance_score, is_safe_public_url, snapshot_hash, text_difference, trend_is_supported)

def test_snapshot_normalizes_noise() -> None:
    assert snapshot_hash('alpha  beta') == snapshot_hash('alpha beta')

def test_difference_reports_changed_words() -> None:
    diff = text_difference('AI testing', 'AI agentic testing')
    assert diff['added'] == ['agentic']

def test_ssrf_protection_blocks_non_public_urls() -> None:
    assert not is_safe_public_url('http://127.0.0.1/admin')
    assert not is_safe_public_url('https://localhost/secret')
    assert is_safe_public_url('https://example.com/docs')

def test_claim_lens_remains_neutral() -> None:
    assert classify_claim('Autonomous, AI-powered testing', False, False)['status'] == 'Marketing-level claim'

def test_evidence_status_does_not_equate_missing_with_unsupported() -> None:
    assert evidence_status('marketing', 0, False) == 'Official marketing claim only'

def test_score_is_explainable_and_deterministic() -> None:
    score = importance_score(100, 100, 100, 100, 100, 100)
    assert score['total'] == 100
    assert score['strategy_relevance'] == 25

def test_trends_need_multiple_strong_signals() -> None:
    assert not trend_is_supported(1, 1)
    assert trend_is_supported(2, 2)
