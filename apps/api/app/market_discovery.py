"""Opt-in market discovery connectors for public launch and funding signals.

Discovery records are *candidates*, not confirmed competitors.  Product Hunt
and Crunchbase both require account-level credentials; this module never
scrapes either service and is intentionally silent when they are not enabled.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from typing import Any

import httpx


PRODUCT_HUNT_ENDPOINT = "https://api.producthunt.com/v2/api/graphql"
CRUNCHBASE_SEARCH_ENDPOINT = "https://api.crunchbase.com/api/v4/data/searches/organizations"
X_RECENT_SEARCH_ENDPOINT = "https://api.x.com/2/tweets/search/recent"
TEST_AUTOMATION_KEYWORDS = (
    "test automation", "automated testing", "software testing", "test management",
    "qa automation", "quality assurance", "self-healing", "playwright", "selenium",
)


def discovery_status() -> dict[str, object]:
    """Expose configuration state without ever returning secret values."""
    return {
        "product_hunt": {
            "enabled": bool(os.getenv("PRODUCT_HUNT_ACCESS_TOKEN", "").strip()),
            "requires": "Product Hunt developer token and commercial-use approval when applicable",
        },
        "crunchbase": {
            "enabled": bool(os.getenv("CRUNCHBASE_API_KEY", "").strip()),
            "requires": "Crunchbase API key with funding-round data access",
        },
        "x": {
            "enabled": bool(os.getenv("X_BEARER_TOKEN", "").strip()),
            "requires": "X developer-app bearer token with recent-search access",
            "coverage": "Recent public posts only (up to the last seven days)",
        },
        "policy": "Candidates and financial claims require a source link and remain unverified until reviewed.",
    }


def format_x_posts(payload: dict[str, Any]) -> list[dict[str, object]]:
    """Convert official X API data into attributable, source-linked records."""
    users = {str(user.get("id")): user for user in payload.get("includes", {}).get("users", [])}
    records: list[dict[str, object]] = []
    for post in payload.get("data", []):
        post_id = str(post.get("id", ""))
        author = users.get(str(post.get("author_id", "")), {})
        username = str(author.get("username", ""))
        if not post_id or not username:
            continue
        metrics = post.get("public_metrics") or {}
        records.append({"id": post_id, "author": username, "text": str(post.get("text", "")), "created_at": str(post.get("created_at", "")), "url": f"https://x.com/{username}/status/{post_id}", "likes": int(metrics.get("like_count", 0)), "reposts": int(metrics.get("retweet_count", 0)), "replies": int(metrics.get("reply_count", 0)), "source": "X API v2 recent search"})
    return records


async def discover_x_posts() -> list[dict[str, object]]:
    """Retrieve attributable public test-automation discussion through X's API."""
    token = os.getenv("X_BEARER_TOKEN", "").strip()
    if not token:
        return []
    params = {"query": '("test automation" OR "automated testing" OR "AI testing" OR playwright OR selenium OR "self-healing tests") lang:en -is:retweet', "max_results": 25, "tweet.fields": "created_at,author_id,public_metrics", "expansions": "author_id", "user.fields": "username"}
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(X_RECENT_SEARCH_ENDPOINT, params=params, headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
    return format_x_posts(response.json())


def _matches_test_automation(*values: str) -> bool:
    text = " ".join(values).lower()
    return any(keyword in text for keyword in TEST_AUTOMATION_KEYWORDS)


async def discover_product_hunt() -> list[dict[str, str]]:
    """Retrieve recent launches and locally retain only relevant candidates."""
    token = os.getenv("PRODUCT_HUNT_ACCESS_TOKEN", "").strip()
    if not token:
        return []
    # The API returns public post metadata. Filtering is deliberately local so
    # we do not imply that Product Hunt has a 'test automation' category.
    query = """
      query RecentLaunches {
        posts(first: 50, order: NEWEST) {
          edges { node { name tagline url website votesCount createdAt } }
        }
      }
    """
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            PRODUCT_HUNT_ENDPOINT,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"query": query},
        )
        response.raise_for_status()
    payload: dict[str, Any] = response.json()
    if payload.get("errors"):
        raise RuntimeError("Product Hunt returned an API error")
    edges = payload.get("data", {}).get("posts", {}).get("edges", [])
    signals: list[dict[str, str]] = []
    for edge in edges:
        node = edge.get("node", {})
        name, tagline = str(node.get("name", "")), str(node.get("tagline", ""))
        if name and _matches_test_automation(name, tagline):
            signals.append({
                "kind": "market_candidate",
                "company": name,
                "title": f"New Product Hunt launch candidate: {name}",
                "summary": tagline or "No Product Hunt tagline supplied.",
                "url": str(node.get("url") or node.get("website") or ""),
                "source": "Product Hunt public launch metadata",
                "status": "candidate — requires analyst verification",
                "detected_at": str(node.get("createdAt") or datetime.now(timezone.utc).isoformat()),
            })
    return signals


async def discover_crunchbase_funding() -> list[dict[str, str]]:
    """Retrieve recent, sourced funding candidates when licensed data is enabled.

    Revenue is not inferred: it is reported only when a source explicitly
    supplies a figure. Crunchbase commonly supplies funding-round information,
    not verified revenue, so revenue remains 'not disclosed' by default.
    """
    key = os.getenv("CRUNCHBASE_API_KEY", "").strip()
    if not key:
        return []
    since = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    request = {
        "field_ids": ["identifier", "short_description", "last_funding_at", "funding_total", "website_url"],
        "query": [{"type": "predicate", "field_id": "last_funding_at", "operator_id": "gte", "values": [since]}],
        "limit": 100,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            CRUNCHBASE_SEARCH_ENDPOINT,
            params={"user_key": key},
            json=request,
        )
        response.raise_for_status()
    entities = response.json().get("entities", [])
    signals: list[dict[str, str]] = []
    for entity in entities:
        properties = entity.get("properties", {})
        identifier = properties.get("identifier", {})
        name = str(identifier.get("value", ""))
        description = str(properties.get("short_description", ""))
        if name and _matches_test_automation(name, description):
            funding = properties.get("funding_total")
            signals.append({
                "kind": "funding_candidate",
                "company": name,
                "title": f"Funding signal: {name}",
                "summary": f"Funding total reported by Crunchbase: {funding}. Revenue: not disclosed by this source.",
                "url": str(properties.get("website_url") or ""),
                "source": "Crunchbase API",
                "status": "third-party funding data — requires verification",
                "detected_at": str(properties.get("last_funding_at") or datetime.now(timezone.utc).isoformat()),
            })
    return signals


async def run_market_discovery() -> dict[str, object]:
    """Run enabled connectors independently; one provider failure never stops collection."""
    status = discovery_status()
    signals: list[dict[str, str]] = []
    failures: list[str] = []
    if status["product_hunt"]["enabled"]:  # type: ignore[index]
        try:
            signals.extend(await discover_product_hunt())
        except Exception:
            failures.append("Product Hunt")
    if status["crunchbase"]["enabled"]:  # type: ignore[index]
        try:
            signals.extend(await discover_crunchbase_funding())
        except Exception:
            failures.append("Crunchbase")
    x_posts: list[dict[str, object]] = []
    if status["x"]["enabled"]:  # type: ignore[index]
        try:
            x_posts = await discover_x_posts()
        except Exception:
            failures.append("X")
    return {"status": status, "signals": signals, "x_posts": x_posts, "failed_providers": failures}
