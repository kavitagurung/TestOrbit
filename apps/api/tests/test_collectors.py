import pytest
from app.collectors import collect_public_page

@pytest.mark.asyncio
async def test_collector_rejects_private_and_disallowed_sources() -> None:
    with pytest.raises(ValueError):
        await collect_public_page('https://127.0.0.1/', 'documentation')
    with pytest.raises(ValueError):
        await collect_public_page('https://example.com/', 'linkedin')

