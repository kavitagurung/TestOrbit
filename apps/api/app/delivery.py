"""One-way Teams payload builder; webhook URLs are intentionally never accepted or logged here."""
from typing import Any

def teams_payload(title: str, summary: str, citations: list[str]) -> dict[str, Any]:
    return {"type": "message", "attachments": [{"contentType": "application/vnd.microsoft.card.adaptive", "content": {"$schema": "http://adaptivecards.io/schemas/adaptive-card.json", "type": "AdaptiveCard", "version": "1.5", "body": [{"type": "TextBlock", "text": title, "weight": "Bolder"}, {"type": "TextBlock", "text": summary, "wrap": True}, {"type": "TextBlock", "text": "Evidence: " + ", ".join(citations), "wrap": True}]}}]}

