"""Deterministic, testable intelligence primitives; untrusted source text is never executed."""
from __future__ import annotations

import hashlib
import ipaddress
import re
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlparse

BLOCKED_HOSTS = {"localhost", "metadata.google.internal"}
CLAIMS = ("ai-powered", "agentic", "autonomous", "self-healing", "zero maintenance", "no-code", "intelligent", "predictive", "enterprise-grade", "end-to-end", "real-time", "production-ready")

def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()

def snapshot_hash(value: str) -> str:
    return hashlib.sha256(normalize_text(value).encode()).hexdigest()

def text_difference(before: str, after: str) -> dict[str, object]:
    before_words, after_words = set(normalize_text(before).lower().split()), set(normalize_text(after).lower().split())
    added, removed = sorted(after_words - before_words), sorted(before_words - after_words)
    universe = len(before_words | after_words) or 1
    return {"added": added, "removed": removed, "magnitude": round((len(added) + len(removed)) / universe * 100, 1)}

def is_safe_public_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return False
    host = parsed.hostname.lower()
    if host in BLOCKED_HOSTS or host.endswith(".local"):
        return False
    try:
        return not ipaddress.ip_address(host).is_private and not ipaddress.ip_address(host).is_loopback
    except ValueError:
        return True

def classify_claim(text: str, has_documentation: bool, has_implementation_evidence: bool) -> dict[str, str]:
    detected = [claim for claim in CLAIMS if claim in text.lower()]
    if has_documentation and has_implementation_evidence:
        status = "Documented capability"
    elif has_documentation:
        status = "Partially evidenced"
    else:
        status = "Marketing-level claim" if detected else "Requires validation"
    return {"status": status, "phrases": ", ".join(detected) or "none"}

def evidence_status(source_type: str, corroborated: int, documented: bool) -> str:
    if documented and source_type == "documentation": return "Confirmed by official documentation"
    if source_type in {"announcement", "release_notes"}: return "Confirmed by official announcement"
    if corroborated >= 2: return "Corroborated by multiple sources"
    return "Official marketing claim only" if source_type == "marketing" else "Unverified"

def importance_score(strategy: int, reliability: int, magnitude: int, competitor: int, corroboration: int, recency: int) -> dict[str, float]:
    parts = {"strategy_relevance": strategy * .25, "source_reliability": reliability * .20, "change_magnitude": magnitude * .20, "competitor_importance": competitor * .15, "cross_source_corroboration": corroboration * .10, "recency": recency * .10}
    return {**{key: round(value, 2) for key, value in parts.items()}, "total": round(sum(parts.values()), 2)}

def weighted_score(parts: dict[str, int]) -> dict[str, object]:
    if not parts: return {"components": {}, "total": 0.0}
    return {"components": parts, "total": round(sum(parts.values()) / len(parts), 2)}

def trend_is_supported(signal_count: int, strong_evidence_count: int) -> bool:
    return signal_count >= 2 and strong_evidence_count >= 2

def safe_ai_input(page_text: str, max_chars: int = 12000) -> str:
    """Delimit untrusted content so it cannot become system instructions."""
    return "UNTRUSTED_SOURCE_CONTENT:\n" + normalize_text(page_text)[:max_chars]

