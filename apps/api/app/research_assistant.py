"""Evidence-first research answers for Ask TestOrbit.

Facts are composed only from the curated evidence records.  AI-style analysis
is deliberately labelled as inference and never used as a source of facts.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import date, timedelta
import json
import re
from typing import Any

from pydantic import BaseModel, Field

from .competitive_analysis import COMPETITOR_EVIDENCE


class ResearchQuery(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    period: str = "90"
    evidence_types: list[str] = Field(default_factory=lambda: ["Official", "Documentation", "Marketing"])
    competitors: list[str] = Field(default_factory=list)


_CACHE: dict[str, dict[str, Any]] = {}
_STOP_WORDS = {"about", "added", "anything", "are", "can", "companies", "competitor", "competitors", "did", "everything", "find", "for", "from", "has", "have", "how", "in", "is", "last", "mention", "most", "on", "show", "support", "the", "this", "to", "what", "which", "who", "with"}


def _records() -> list[dict[str, str]]:
    source_types = {
        "Functionize": ("Official", "Functionize official blog"),
        "UiPath": ("Documentation", "UiPath Agents release notes"),
        "SmartBear TestComplete": ("Documentation", "SmartBear TestComplete release notes"),
        "Tricentis Tosca": ("Documentation", "Tricentis Tosca Cloud release notes"),
        "Opkey": ("Marketing", "Opkey official blog"),
    }
    return [
        {
            **item,
            "evidence_type": source_types[item["vendor"]][0],
            "source_name": source_types[item["vendor"]][1],
            "citation_id": f"src-{index + 1}",
        }
        for index, item in enumerate(COMPETITOR_EVIDENCE)
    ]


def _cutoff(period: str) -> date | None:
    if period == "all":
        return None
    days = {"30": 30, "90": 90, "365": 365}.get(period, 90)
    return date.today() - timedelta(days=days)


def retrieve(query: ResearchQuery) -> list[dict[str, str]]:
    question = query.question.lower()
    words = {word for word in re.findall(r"[a-z0-9]+", question) if len(word) > 2 and word not in _STOP_WORDS}
    broad_query = any(phrase in question for phrase in ("what changed", "show everything", "all competitors", "last month", "last week"))
    requested_competitors = {item.lower() for item in query.competitors}
    cutoff = _cutoff(query.period)
    matched: list[dict[str, str]] = []
    for item in _records():
        if item["evidence_type"] not in query.evidence_types:
            continue
        if cutoff and date.fromisoformat(item["date"]) < cutoff:
            continue
        haystack = " ".join(item[key].lower() for key in ("vendor", "feature", "detail"))
        vendor_match = item["vendor"].lower() in question or item["vendor"].lower() in requested_competitors
        keyword_match = bool(words & set(re.findall(r"[a-z0-9]+", haystack)))
        if broad_query or vendor_match or keyword_match:
            matched.append(item)
    return matched


def _confidence(records: list[dict[str, str]]) -> tuple[str, str]:
    official = [record for record in records if record["evidence_type"] != "Marketing"]
    if len(official) >= 3:
        return "High", f"Based on {len(official)} independent official or documentation sources."
    if official:
        return "Medium", "Based on a limited number of official or documentation sources."
    return "Low", "Only marketing evidence is available; no independent product documentation was found."


def _follow_ups(records: list[dict[str, str]]) -> list[str]:
    if not records:
        return ["Expand the search period", "Search all competitors", "Show official documentation only"]
    vendor = records[0]["vendor"]
    return [f"How does this compare with {vendor}?", "Show supporting evidence", "What changed in the last year?"]


def answer(query: ResearchQuery) -> dict[str, Any]:
    cache_key = json.dumps(query.model_dump(), sort_keys=True)
    if cache_key in _CACHE:
        return {**_CACHE[cache_key], "cached": True}
    records = retrieve(query)
    if not records:
        result = {
            "summary": "No evidence found.",
            "verified_facts": [],
            "analysis": "This is an inference based on available evidence: no direction can be inferred because the filtered evidence set is empty.",
            "missing_evidence": "No verified evidence currently exists for this question in the selected period and evidence types. Add an official release note, documentation page, or newsroom source to answer it safely.",
            "confidence": {"level": "Low", "reason": "No matching stored evidence was retrieved."},
            "sources": [],
            "timeline": [],
            "follow_ups": _follow_ups(records),
            "cached": False,
        }
        _CACHE[cache_key] = result
        return result
    confidence, confidence_reason = _confidence(records)
    facts = [
        {
            "text": f"{record['vendor']} — {record['detail']}",
            "citation_id": record["citation_id"],
        }
        for record in records
    ]
    vendors = ", ".join(record["vendor"] for record in records)
    feature_list = ", ".join(record["feature"] for record in records[:3])
    result = {
        "summary": f"{len(records)} stored evidence record{'s' if len(records) != 1 else ''} match your question: {vendors}.",
        "verified_facts": facts,
        "analysis": f"This is an inference based on available evidence: the matching updates cluster around {feature_list}. This indicates visible product attention, not proof of adoption, market share, or commercial success.",
        "missing_evidence": "No independent adoption, pricing, customer-outcome, or implementation evidence was retrieved. Additional primary sources would be needed for those claims.",
        "confidence": {"level": confidence, "reason": confidence_reason},
        "sources": [
            {"citation_id": record["citation_id"], "name": record["source_name"], "type": record["evidence_type"], "url": record["url"], "date_collected": record["date"]}
            for record in records
        ],
        "timeline": [{"date": record["date"], "vendor": record["vendor"], "event": record["feature"], "citation_id": record["citation_id"]} for record in records],
        "follow_ups": _follow_ups(records),
        "cached": False,
    }
    _CACHE[cache_key] = result
    return result


async def stream_answer(query: ResearchQuery) -> AsyncIterator[str]:
    """SSE stream with visible summary tokens followed by a complete trusted payload."""
    result = answer(query)
    yield f"event: start\ndata: {json.dumps({'cached': result['cached']})}\n\n"
    for token in re.findall(r"\S+\s*", result["summary"]):
        yield f"event: summary_delta\ndata: {json.dumps({'text': token})}\n\n"
        await asyncio.sleep(0.012)
    yield f"event: complete\ndata: {json.dumps(result)}\n\n"
