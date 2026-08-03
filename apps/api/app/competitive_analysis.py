"""Evidence-grounded competitor analysis with an optional server-side OpenAI pass."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import json
import os
from typing import Any

import httpx


COMPETITOR_EVIDENCE = [
    {"vendor": "Functionize", "date": "2026-07-16", "feature": "Adversarial AI quality evaluation", "detail": "Functionize announced general availability of Studio, an adversarial AI agent for evaluating software quality.", "url": "https://www.functionize.com/blog/meet-functionize-studio"},
    {"vendor": "UiPath", "date": "2026-07-24", "feature": "AI-agent escalation routing", "detail": "UiPath added workload, group, round-robin, and LLM-inferred routing for agent escalations.", "url": "https://docs.uipath.com/agents/automation-cloud/latest/release-notes/july-2026"},
    {"vendor": "SmartBear TestComplete", "date": "2026-07-08", "feature": "UI-test reliability", "detail": "TestComplete 15.83 includes object-recognition, recording reliability, browser compatibility, and stability improvements.", "url": "https://support.smartbear.com/testcomplete/docs/general-info/whats-new.html"},
    {"vendor": "Tricentis Tosca", "date": "2026-07-28", "feature": "Prompt-based API test design", "detail": "Tosca Cloud release notes describe generating API messages from a prompt through MCP.", "url": "https://docs.tricentis.com/tosca-cloud/en-us/content/release_notes/release_notes.htm"},
    {"vendor": "Opkey", "date": "2026-07-09", "feature": "AI-enabled ERP release analysis", "detail": "Opkey published a positioning claim about agentic AI for Oracle and Workday release analysis; it is not treated as a confirmed product release.", "url": "https://www.opkey.com/blog/leveraging-ai-in-workday-testing-ensuring-quality-and-efficiency"},
]

_CACHE: dict[int, tuple[datetime, dict[str, Any]]] = {}


def _feature_leaders(evidence: list[dict[str, str]]) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = {}
    for item in evidence:
        groups.setdefault(item["feature"], []).append(item["vendor"])
    return [
        {"feature": feature, "vendors": vendors, "vendor_count": len(vendors)}
        for feature, vendors in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))
    ]


def fallback_analysis(evidence: list[dict[str, str]], range_days: int) -> dict[str, Any]:
    vendors = ", ".join(item["vendor"] for item in evidence)
    return {
        "mode": "rule_based_fallback",
        "range_days": range_days,
        "summary": f"{len(evidence)} official competitor updates were tracked in the last {range_days} days across {vendors}. The visible themes are AI-assisted testing operations, quality evaluation, UI-test reliability, and API-test authoring.",
        "themes": [
            "AI-assisted testing and agent operations are the strongest recurring public theme.",
            "Competitors are pairing AI claims with core test-authoring or test-execution workflows.",
            "Opkey’s item is labelled as positioning rather than a verified new product capability.",
        ],
        "feature_leaders": _feature_leaders(evidence),
        "recommendations": [
            {
                "title": "AI-guided release impact assessment",
                "market_fit_signal": 78,
                "rationale": "Multiple public updates emphasise agentic testing, exception handling, or ERP release analysis. A focused workflow that explains release impact and guides regression review has strong visible market alignment.",
                "evidence_vendors": ["Functionize", "UiPath", "Opkey"],
            },
            {
                "title": "Natural-language API test design",
                "market_fit_signal": 66,
                "rationale": "Prompt-based API message creation is appearing in public product updates, indicating demand for reducing manual setup during API test authoring.",
                "evidence_vendors": ["Tricentis Tosca"],
            },
            {
                "title": "Locator resilience and change evidence",
                "market_fit_signal": 64,
                "rationale": "Reliability, object recognition, and release analysis are recurring concerns. A feature that shows before-and-after UI evidence before suggesting a locator fix would be differentiated and directly actionable.",
                "evidence_vendors": ["SmartBear TestComplete", "Opkey"],
            },
        ],
        "evidence": evidence,
    }


def _response_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    for output in payload.get("output", []):
        for content in output.get("content", []):
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                return content["text"]
    return ""


async def analyze_competitors(range_days: int = 90) -> dict[str, Any]:
    """Return cached, evidence-bound analysis. No client-supplied text reaches the model."""
    cutoff = date.today() - timedelta(days=range_days)
    evidence = [item for item in COMPETITOR_EVIDENCE if date.fromisoformat(item["date"]) >= cutoff]
    baseline = fallback_analysis(evidence, range_days)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not evidence:
        return baseline

    cached = _CACHE.get(range_days)
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
        "model": os.getenv("OPENAI_MODEL", "gpt-5.6-sol"),
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
        model_result = json.loads(_response_text(response.json()))
        recommendations = model_result.get("recommendations", baseline["recommendations"])
        result = {**baseline, "mode": "openai", "summary": str(model_result["summary"]), "themes": [str(theme) for theme in model_result["themes"][:3]], "recommendations": recommendations[:3]}
        _CACHE[range_days] = (now, result)
        return result
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return baseline
