"""Curated public evidence used by the initial live-intelligence slice.

Entries are verified against the cited official URL.  They deliberately keep
marketing claims distinct from documented capabilities and do not infer a
release date where the source does not provide one.
"""
from datetime import date
from pydantic import BaseModel, HttpUrl

class EvidenceSignal(BaseModel):
    id: str
    competitor: str
    product: str
    title: str
    summary: str
    category: str
    evidence_status: str
    source_type: str
    source_url: HttpUrl
    publication_date: date | None = None
    first_detected_date: date
    last_verified_date: date
    confidence: int
    fact: str
    inference: str | None = None

VERIFIED_SIGNALS = [
    EvidenceSignal(
        id="live-uipath-2026-07-test-manager",
        competitor="UiPath",
        product="UiPath Test Cloud / Test Manager",
        title="Test with Coding Agents listed as preview",
        summary="UiPath’s July platform release notes list a preview that lets a coding agent read Test Manager test cases, results, and coverage, write results and metadata, and trigger and monitor test sets from a terminal.",
        category="AI and agentic testing",
        evidence_status="Confirmed by official documentation",
        source_type="official release notes",
        source_url="https://docs.uipath.com/release-notes/other/latest/release-notes/cloud-platform-july-2026",
        publication_date=date(2026, 7, 15),
        first_detected_date=date(2026, 8, 1),
        last_verified_date=date(2026, 8, 1),
        confidence=92,
        fact="UiPath documents this Test Manager capability as preview in its official July 2026 release notes.",
        inference="Product teams may want to investigate how terminal- and coding-agent-driven test operations affect buyer expectations; this is an inference, not a confirmed market trend.",
    ),
    EvidenceSignal(
        id="live-opkey-release-advisor",
        competitor="Opkey",
        product="Opkey Release Advisor",
        title="Release Advisor positioned for Oracle and Workday release analysis",
        summary="Opkey’s public newsroom presents Release Advisor as using agentic AI to speed Oracle and Workday release analysis.",
        category="Agentic testing claim",
        evidence_status="Official marketing claim only",
        source_type="official newsroom",
        source_url="https://www.opkey.com/news",
        publication_date=None,
        first_detected_date=date(2026, 8, 1),
        last_verified_date=date(2026, 8, 1),
        confidence=68,
        fact="Opkey makes this positioning claim on its official newsroom.",
        inference="Implementation details and independent validation were not assessed in this initial signal, so the claim requires validation before it is treated as a documented capability.",
    ),
]

# These are official, public release-watch references.  A publication can
# indicate where regression attention is prudent, but it cannot prove that a
# selector has changed in a customer's authenticated tenant.
ENTERPRISE_RELEASE_WATCH = [
    {
        "vendor": "Workday",
        "update": "Agent Passport was announced for testing, verifying, and continuously monitoring enterprise AI agents.",
        "impact": "Potential test impact: review agent approvals, policy enforcement, and runtime exception paths. No selector change is confirmed from the public announcement.",
        "url": "https://newsroom.workday.com/2026-06-02-Workday-Launches-Agent-Passport-to-Test%2C-Verify%2C-and-Continuously-Monitor-Every-AI-Agent-in-the-Enterprise",
    },
    {
        "vendor": "Coupa",
        "update": "Coupa Supplier Portal release notes are under active release watch.",
        "impact": "Potential selector risk: when a relevant portal release is detected, revalidate impacted UI paths in an approved tenant. Public monitoring alone cannot confirm a selector change.",
        "url": "https://docs.coupa.com/en/supplier-documentation/coupa-for-suppliers/announcements-and-general-information/coupa-supplier-portal-release-notes",
    },
]

def daily_slack_brief(changes: list[dict[str, str]]) -> tuple[str, list[str]]:
    """Create an understandable, evidence-linked daily Slack briefing."""
    uipath, opkey = VERIFIED_SIGNALS
    workday, coupa = ENTERPRISE_RELEASE_WATCH
    detected = "No newly detected source-content changes since the last run. The latest verified intelligence is below."
    if changes:
        detected = "New source-content changes were detected today: " + "; ".join(
            f"{change['competitor']} — {change['title']}" for change in changes
        )
    summary = "\n".join([
        "Hi Kavita 👋",
        "*Your daily competitive research and analysis is ready.*",
        "",
        "*New in test automation*",
        f"• *UiPath* — {uipath.summary} _Published 15 Jul 2026; verified official release notes._",
        f"• *Opkey* — {opkey.summary} _Official positioning claim; implementation details still require validation._",
        "",
        "*Enterprise release watch*",
        f"• *Workday* — {workday['update']} {workday['impact']}",
        f"• *Coupa* — {coupa['update']} {coupa['impact']}",
        "",
        "*Today’s collection result*",
        detected,
        "",
        "_Evidence links are included below. TestOrbit labels potential UI/selector impact as an inference until it is verified in an authorized test environment._",
    ])
    citations = [
        str(uipath.source_url),
        str(opkey.source_url),
        workday["url"],
        coupa["url"],
        *[change["url"] for change in changes],
    ]
    return summary, citations

def today_summary(today: date = date.today()) -> dict[str, object]:
    today_signals = [signal for signal in VERIFIED_SIGNALS if signal.publication_date == today]
    if not today_signals:
        headline = "No newly verified Opkey or UiPath feature release was found for today in the configured official sources."
    else:
        headline = f"{len(today_signals)} officially dated competitor release(s) were verified today."
    return {"as_of": today, "headline": headline, "signals": VERIFIED_SIGNALS, "source_scope": "Initial curated official-source coverage: Opkey newsroom and UiPath release notes."}
