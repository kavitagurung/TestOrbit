"""One-way Teams delivery; webhook URLs are read only from server-side environment."""
import os
from urllib.parse import urlparse
from typing import Any
import httpx

def teams_payload(title: str, summary: str, citations: list[str]) -> dict[str, Any]:
    return {"type": "message", "attachments": [{"contentType": "application/vnd.microsoft.card.adaptive", "content": {"$schema": "http://adaptivecards.io/schemas/adaptive-card.json", "type": "AdaptiveCard", "version": "1.5", "body": [{"type": "TextBlock", "text": title, "weight": "Bolder"}, {"type": "TextBlock", "text": summary, "wrap": True}, {"type": "TextBlock", "text": "Evidence: " + ", ".join(citations), "wrap": True}]}}]}

def configured_teams_webhook() -> str | None:
    value = os.getenv("TEAMS_WEBHOOK_URL", "").strip()
    host = urlparse(value).hostname or ""
    if value.startswith("https://") and (host.endswith(".logic.azure.com") or host.endswith(".webhook.office.com")):
        return value
    return None

async def post_teams_notification(title: str, summary: str, citations: list[str]) -> bool:
    """Send a bounded Adaptive Card without logging URL, headers, or payload contents."""
    webhook = configured_teams_webhook()
    if not webhook:
        return False
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(webhook, json=teams_payload(title, summary, citations))
        response.raise_for_status()
    return True
