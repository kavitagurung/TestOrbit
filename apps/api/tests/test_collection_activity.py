from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app import database
from app.collection_activity import collection_activity


def test_activity_reads_database_and_distinguishes_baselines(monkeypatch):
    engine = create_engine('sqlite://', poolclass=StaticPool)
    database.Base.metadata.create_all(engine)
    monkeypatch.setattr(database, 'SessionLocal', sessionmaker(bind=engine))
    assert collection_activity()['items'] == []
    with database.session_scope() as session:
        source = database.Source(competitor='UiPath', product='Cloud', name='Release notes', url='https://docs.uipath.com/', source_type='release_notes')
        session.add(source)
        session.flush()
        session.add_all([
            database.Snapshot(source_id=source.id, content_hash='a', excerpt='baseline', collected_at=datetime(2026, 9, 30)),
            database.Snapshot(source_id=source.id, content_hash='b', excerpt='changed', collected_at=datetime(2026, 10, 1)),
        ])
    items = collection_activity()['items']
    assert [item['kind'] for item in items] == ['content_changed', 'baseline']
    assert items[0]['detected_at'] == '2026-10-01T00:00:00+00:00'
    assert items[0]['source_url'] == 'https://docs.uipath.com/'
    assert 'excerpt' not in items[0]
