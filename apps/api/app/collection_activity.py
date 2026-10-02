"""Read-only activity from stored public-source snapshots, without claiming verification."""
from datetime import timezone
from sqlalchemy import func, select
from .database import Snapshot, Source, session_scope


def collection_activity() -> dict[str, object]:
    with session_scope() as session:
        first_snapshot = select(Snapshot.source_id, func.min(Snapshot.id).label('first_id')).group_by(Snapshot.source_id).subquery()
        rows = session.execute(
            select(Snapshot, Source, first_snapshot.c.first_id)
            .join(Source, Source.id == Snapshot.source_id)
            .join(first_snapshot, first_snapshot.c.source_id == Source.id)
            .order_by(Snapshot.collected_at.desc(), Snapshot.id.desc()).limit(30)
        ).all()
        items = [{
            'id': snapshot.id,
            'competitor': source.competitor,
            'source_name': source.name,
            'source_url': source.url,
            'detected_at': snapshot.collected_at.replace(tzinfo=timezone.utc).isoformat(),
            'kind': 'baseline' if snapshot.id == first_id else 'content_changed',
        } for snapshot, source, first_id in rows]
    return {'items': items, 'scope': 'Stored public-source snapshots. Baselines and content changes are not verified product releases. Unchanged checks do not create snapshots.'}
