"""Public-source collector guardrails. Fetching is deliberately opt-in and bounded."""
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from .intelligence import is_safe_public_url, normalize_text

MAX_RESPONSE_BYTES = 1_000_000
ALLOWED_SOURCE_TYPES = {"homepage", "product_page", "documentation", "release_notes", "changelog", "blog", "pricing", "github", "rss", "status"}

async def collect_public_page(url: str, source_type: str) -> dict[str, str]:
    if source_type not in ALLOWED_SOURCE_TYPES or not is_safe_public_url(url):
        raise ValueError("Source is not an allowed public HTTPS URL")
    async with httpx.AsyncClient(timeout=10, follow_redirects=True, headers={"User-Agent": "TestOrbit/0.1 public research"}) as client:
        response = await client.get(url)
        response.raise_for_status()
        content = response.content[:MAX_RESPONSE_BYTES]
    text = normalize_text(BeautifulSoup(content, "html.parser").get_text(" "))
    return {"url": str(response.url), "domain": urlparse(str(response.url)).hostname or "", "text": text, "truncated": str(len(response.content) > MAX_RESPONSE_BYTES).lower()}

