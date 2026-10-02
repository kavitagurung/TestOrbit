from app.daily_collection import INITIAL_SOURCES

def test_initial_sources_are_public_and_competitor_scoped() -> None:
    assert {source['competitor'] for source in INITIAL_SOURCES} == {
        'UiPath', 'Opkey', 'Coupa', 'Workday', 'ServiceNow', 'SAP SuccessFactors'
    }
    assert all(source['url'].startswith('https://') for source in INITIAL_SOURCES)

import httpx
import pytest
from unittest.mock import AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app import database, daily_collection

@pytest.mark.asyncio
async def test_failed_source_is_visible_without_losing_successful_snapshots(monkeypatch, caplog):
    engine = create_engine('sqlite://', poolclass=StaticPool)
    database.Base.metadata.create_all(engine)
    monkeypatch.setattr(database, 'SessionLocal', sessionmaker(bind=engine))
    monkeypatch.setattr(daily_collection, 'INITIAL_SOURCES', daily_collection.INITIAL_SOURCES[:2])
    async def collect(url, source_type):
        if 'opkey' in url:
            response = httpx.Response(403, request=httpx.Request('GET', url))
            response.raise_for_status()
        return {'text': 'public source evidence'}
    monkeypatch.setattr(daily_collection, 'collect_public_page', collect)
    monkeypatch.setattr(daily_collection, 'run_market_discovery', AsyncMock(return_value={'signals': []}))
    delivery = AsyncMock(return_value=True)
    monkeypatch.setattr(daily_collection, 'post_slack_notification', delivery)
    result = await daily_collection.run_daily_collection(send_slack=False)
    assert result['failed_sources'] == ['Opkey']
    assert result['failure_details'][0]['status_code'] == 403
    assert result['baselines_created'] == 1
    assert 'status=403' in caplog.text
    delivery.assert_not_awaited()
