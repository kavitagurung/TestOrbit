"""Observable daily public-source collector with deterministic baseline/difference behavior."""
from datetime import datetime

from sqlalchemy import select

from .collectors import collect_public_page
from .database import Snapshot, Source, session_scope
from .intelligence import snapshot_hash
from .live_intelligence import daily_slack_brief
from .market_discovery import run_market_discovery
from .slack_delivery import post_slack_notification

INITIAL_SOURCES = [
    {"competitor": "UiPath", "product": "UiPath Test Cloud / Test Manager", "name": "UiPath cloud and Test Cloud release notes", "url": "https://docs.uipath.com/release-notes/other/latest/release-notes/cloud-platform-july-2026", "source_type": "release_notes"},
    {"competitor": "Opkey", "product": "Opkey", "name": "Opkey newsroom", "url": "https://www.opkey.com/news", "source_type": "blog"},
    {"competitor": "Coupa", "product": "Coupa Supplier Portal", "name": "Coupa Supplier Portal release notes", "url": "https://docs.coupa.com/en/supplier-documentation/coupa-for-suppliers/announcements-and-general-information/coupa-supplier-portal-release-notes", "source_type": "documentation"},
    {"competitor": "Workday", "product": "Workday", "name": "Workday product releases and innovation", "url": "https://www.workday.com/en-us/products/releases-and-innovation.html", "source_type": "documentation"},
    {"competitor": "Workday", "product": "Workday", "name": "Workday newsroom", "url": "https://newsroom.workday.com/", "source_type": "blog"},
    {"competitor": "ServiceNow", "product": "ServiceNow AI Platform", "name": "ServiceNow latest release", "url": "https://www.servicenow.com/platform/latest-release.html", "source_type": "release_notes"},
    {"competitor": "SAP SuccessFactors", "product": "SAP SuccessFactors", "name": "SAP SuccessFactors release information", "url": "https://help.sap.com/docs/successfactors-release-information", "source_type": "release_notes"},
]

def ensure_initial_sources() -> None:
    with session_scope() as session:
        for item in INITIAL_SOURCES:
            if not session.scalar(select(Source).where(Source.url == item["url"])):
                session.add(Source(**item))

async def run_daily_collection(send_slack: bool = True) -> dict[str, object]:
    ensure_initial_sources()
    with session_scope() as session:
        # Keep the fields used by the asynchronous collector after the session
        # closes.  ORM instances expire on commit, so carrying them outside this
        # block can cause DetachedInstanceError during scheduled runs.
        sources = [
            {
                "id": source.id,
                "competitor": source.competitor,
                "name": source.name,
                "url": source.url,
                "source_type": source.source_type,
            }
            for source in session.scalars(select(Source)).all()
        ]
    changes: list[dict[str, str]] = []
    failures: list[str] = []
    baselines = 0
    for source in sources:
        try:
            page = await collect_public_page(source["url"], source["source_type"])
            current_hash = snapshot_hash(page["text"])
            with session_scope() as session:
                latest = session.scalar(select(Snapshot).where(Snapshot.source_id == source["id"]).order_by(Snapshot.collected_at.desc()))
                if latest is None:
                    baselines += 1
                elif latest.content_hash != current_hash:
                    changes.append({"competitor": source["competitor"], "title": f"Public source content changed: {source['name']}", "url": source["url"]})
                if latest is None or latest.content_hash != current_hash:
                    session.add(Snapshot(source_id=source["id"], content_hash=current_hash, excerpt=page["text"][:4000]))
        except Exception:
            failures.append(source["competitor"])
    discovery = await run_market_discovery()
    delivered = False
    if send_slack:
        summary, citations = daily_slack_brief(changes)
        candidates = discovery["signals"]
        if candidates:
            names = ", ".join(signal["company"] for signal in candidates[:5])
            summary += f"\n\nMarket discovery candidates (review required): {names}."
            citations += [signal["url"] for signal in candidates[:5] if signal["url"]]
        delivered = await post_slack_notification("TestOrbit daily competitive research", summary, citations)
    return {"collected_at": datetime.utcnow().isoformat(), "sources_checked": len(sources), "baselines_created": baselines, "changes": changes, "failed_sources": failures, "market_discovery": discovery, "slack_delivered": delivered}
