"""Observable daily public-source collector with deterministic baseline/difference behavior."""
from datetime import datetime

from sqlalchemy import select

from .collectors import collect_public_page
from .database import Snapshot, Source, session_scope
from .intelligence import snapshot_hash
from .slack_delivery import post_slack_notification

INITIAL_SOURCES = [
    {"competitor": "UiPath", "product": "UiPath Test Cloud / Test Manager", "name": "UiPath cloud and Test Cloud release notes", "url": "https://docs.uipath.com/release-notes/other/latest/release-notes/cloud-platform-july-2026", "source_type": "release_notes"},
    {"competitor": "Opkey", "product": "Opkey", "name": "Opkey newsroom", "url": "https://www.opkey.com/news", "source_type": "blog"},
]

def ensure_initial_sources() -> None:
    with session_scope() as session:
        for item in INITIAL_SOURCES:
            if not session.scalar(select(Source).where(Source.url == item["url"])):
                session.add(Source(**item))

async def run_daily_collection(send_slack: bool = True) -> dict[str, object]:
    ensure_initial_sources()
    with session_scope() as session:
        sources = list(session.scalars(select(Source)).all())
    changes: list[dict[str, str]] = []
    failures: list[str] = []
    baselines = 0
    for source in sources:
        try:
            page = await collect_public_page(source.url, source.source_type)
            current_hash = snapshot_hash(page["text"])
            with session_scope() as session:
                latest = session.scalar(select(Snapshot).where(Snapshot.source_id == source.id).order_by(Snapshot.collected_at.desc()))
                if latest is None:
                    baselines += 1
                elif latest.content_hash != current_hash:
                    changes.append({"competitor": source.competitor, "title": f"Public source content changed: {source.name}", "url": source.url})
                if latest is None or latest.content_hash != current_hash:
                    session.add(Snapshot(source_id=source.id, content_hash=current_hash, excerpt=page["text"][:4000]))
        except Exception:
            failures.append(source.competitor)
    delivered = False
    if send_slack:
        if changes:
            lines = "\n".join(f"• {change['competitor']}: {change['title']}" for change in changes)
            delivered = await post_slack_notification("TestOrbit daily change digest", lines, [change["url"] for change in changes])
        else:
            delivered = await post_slack_notification("TestOrbit daily change digest", "No newly detected changes in the configured public sources. Baselines and source health were checked.", [])
    return {"collected_at": datetime.utcnow().isoformat(), "sources_checked": len(sources), "baselines_created": baselines, "changes": changes, "failed_sources": failures, "slack_delivered": delivered}

