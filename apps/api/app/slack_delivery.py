"""One-way Slack incoming-webhook delivery, configured only on the server."""
import os
from urllib.parse import urlparse

import httpx

def configured_slack_webhook() -> str | None:
    value = os.getenv("SLACK_WEBHOOK_URL", "").strip()
    host = urlparse(value).hostname or ""
    if value.startswith("https://") and (host == "hooks.slack.com" or host.endswith(".hooks.slack.com")):
        return value
    return None

def slack_payload(title: str, summary: str, citations: list[str]) -> dict[str, object]:
    evidence = " • ".join(citations) if citations else "No evidence links supplied"
    return {
        "text": title,
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": title[:150]}},
            {"type": "section", "text": {"type": "mrkdwn", "text": summary[:2800]}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": f"Evidence: {evidence[:2800]}"}]},
        ],
    }

async def post_slack_notification(title: str, summary: str, citations: list[str]) -> bool:
    webhook = configured_slack_webhook()
    if not webhook:
        return False
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(webhook, json=slack_payload(title, summary, citations))
        response.raise_for_status()
    return True
