"""Evidence-grounded competitor analysis with an optional server-side OpenAI pass."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import json
import logging
import os
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field


COMPETITOR_EVIDENCE = [
    {"vendor": "Functionize", "date": "2026-07-16", "feature": "Adversarial AI quality evaluation", "detail": "Functionize announced general availability of Studio, an adversarial AI agent for evaluating software quality.", "url": "https://www.functionize.com/blog/meet-functionize-studio"},
    {"vendor": "UiPath", "date": "2026-07-24", "feature": "AI-agent escalation routing", "detail": "UiPath added workload, group, round-robin, and LLM-inferred routing for agent escalations.", "url": "https://docs.uipath.com/agents/automation-cloud/latest/release-notes/july-2026"},
    {"vendor": "SmartBear TestComplete", "date": "2026-07-08", "feature": "UI-test reliability", "detail": "TestComplete 15.83 includes object-recognition, recording reliability, browser compatibility, and stability improvements.", "url": "https://support.smartbear.com/testcomplete/docs/general-info/whats-new.html"},
    {"vendor": "Tricentis Tosca", "date": "2026-07-28", "feature": "Prompt-based API test design", "detail": "Tosca Cloud release notes describe generating API messages from a prompt through MCP.", "url": "https://docs.tricentis.com/tosca-cloud/en-us/content/release_notes/release_notes.htm"},
    {"vendor": "Opkey", "date": "2026-07-09", "feature": "AI-enabled ERP release analysis", "detail": "Opkey published a positioning claim about agentic AI for Oracle and Workday release analysis; it is not treated as a confirmed product release.", "url": "https://www.opkey.com/blog/leveraging-ai-in-workday-testing-ensuring-quality-and-efficiency"},
]

logger = logging.getLogger(__name__)
_CACHE: dict[tuple[int, str, str], tuple[datetime, dict[str, Any]]] = {}

class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: str = Field(min_length=1)
    market_fit_signal: int = Field(ge=0, le=100)
    rationale: str = Field(min_length=1)
    evidence_vendors: list[str] = Field(min_length=1)

class Synthesis(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    summary: str = Field(min_length=1)
    themes: list[str] = Field(max_length=3)
    recommendations: list[Recommendation] = Field(max_length=3)

def _feature_leaders(evidence: list[dict[str, str]]) -> list[dict[str, Any]]:
    groups: dict[str, set[str]] = {}
    for item in evidence:
        groups.setdefault(item["feature"], set()).add(item["vendor"])
    return [
        {"feature": feature, "vendors": sorted(vendors), "vendor_count": len(vendors)}
        for feature, vendors in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))
    ]

def fallback_analysis(evidence: list[dict[str, str]], range_days: int) -> dict[str, Any]:
    vendors = ", ".join(sorted({item["vendor"] for item in evidence}))
    return {
        "mode": "rule_based_fallback",
        "range_days": range_days,
        "data_scope": "curated_seed",
        "summary": (
            f"{len(evidence)} curated updates fall within the last {range_days} days: {vendors}. "
            "This is a saved evidence set, not a live market scan."
            if evidence else
            f"No curated evidence falls within the last {range_days} days. "
            "This does not establish that no market updates occurred."
        ),
        "themes": [],
        "feature_leaders": _feature_leaders(evidence),
        # Do not manufacture market trends or opportunity percentages from fixed templates.
        "recommendations": [],
        "evidence": evidence,
    }


def _response_text(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        raise ValueError("Expected a response object")
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    for output in payload.get("output", []):
        if not isinstance(output, dict):
            raise ValueError("Invalid output item")
        for content in output.get("content", []):
            if not isinstance(content, dict):
                raise ValueError("Invalid content item")
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                return content["text"]
    return ""


async def analyze_competitors(range_days: int = 90) -> dict[str, Any]:
    """Return cached, evidence-bound analysis. No client-supplied text reaches the model."""
    today = date.today()
    cutoff = today - timedelta(days=range_days)
    evidence = [item for item in COMPETITOR_EVIDENCE if cutoff <= date.fromisoformat(item["date"]) <= today]
    baseline = fallback_analysis(evidence, range_days)
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "").strip()
    if not evidence:
        return {**baseline, "fallback_reason": "no_evidence"}
    if not api_key:
        return {**baseline, "fallback_reason": "not_configured"}
    if not model:
        return {**baseline, "fallback_reason": "model_not_configured"}

    cache_key = (range_days, model, json.dumps(evidence, sort_keys=True))
    cached = _CACHE.get(cache_key)
    now = datetime.now(timezone.utc)
    if cached and now - cached[0] < timedelta(hours=6):
        return cached[1]

    prompt = (
        "Write a concise competitive-intelligence analysis using only the evidence JSON below. "
        "Do not invent features, dates, availability, customer outcomes, or market trends. "
        "Keep positioning claims explicitly labelled. Return JSON with keys summary (string), themes (array of up to 3 strings), and recommendations (array of up to 3 objects with title, market_fit_signal integer 0-100, rationale, and evidence_vendors). A market_fit_signal is only a relative evidence-based opportunity score, never a revenue or success forecast.\n\n"
        + json.dumps(evidence)
    )
    request = {
        "model": model,
        "text": {"format": {"type": "json_object"}},
        "store": False,
        "input": prompt,
    }
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=request,
            )
            response.raise_for_status()
        model_result = Synthesis.model_validate(json.loads(_response_text(response.json())))
        allowed_vendors = {item["vendor"] for item in evidence}
        if any(not set(item.evidence_vendors) <= allowed_vendors for item in model_result.recommendations):
            raise ValueError("Recommendation cites a vendor outside the selected evidence")
        result = {**baseline, **model_result.model_dump(), "mode": "openai"}
        _CACHE[cache_key] = (now, result)
        return result
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        reason = {401: "authentication_failed", 403: "access_denied", 404: "model_unavailable", 429: "rate_or_quota_limit"}.get(status_code, "provider_error")
        logger.warning("Competitive analysis fallback: %s (HTTP %s)", reason, status_code)
    except httpx.TimeoutException:
        reason = "provider_timeout"
        logger.warning("Competitive analysis fallback: provider_timeout")
    except httpx.HTTPError:
        reason = "provider_unavailable"
        logger.warning("Competitive analysis fallback: provider_unavailable")
    except (ValueError, KeyError, TypeError):
        reason = "invalid_response"
        logger.warning("Competitive analysis fallback: invalid_response")
    return {**baseline, "fallback_reason": reason}
