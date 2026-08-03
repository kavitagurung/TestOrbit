from datetime import date
import hmac
import os
from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .intelligence import classify_claim, importance_score, weighted_score
from .live_intelligence import EvidenceSignal, today_summary
from .competitive_analysis import analyze_competitors
from .delivery import post_teams_notification
from .slack_delivery import post_slack_notification
from .database import init_database
from .daily_collection import run_daily_collection
from .automation import collection_due, get_schedule, mark_collected, require_owner, update_schedule
from .github_oidc import verify_scheduler_oidc

app = FastAPI(title="TestOrbit API", version="0.1.0", description="Synthetic demo API. No confidential data.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://kavitagurung.github.io", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

@app.on_event("startup")
def initialize_storage() -> None:
    init_database()

class Health(BaseModel):
    status: str = "ok"
    mode: str = "synthetic-demo"

class Signal(BaseModel):
    id: str
    competitor: str
    category: str
    title: str
    first_detected: date
    confidence: int = Field(ge=0, le=100)
    evidence_status: str

class ScheduleInput(BaseModel):
    frequency: str = "daily"
    day_of_week: str = "Monday"
    time_ist: str = "09:00"
    slack_enabled: bool = True

def schedule_payload(schedule: object) -> dict[str, object]:
    return {"frequency": schedule.frequency, "day_of_week": schedule.day_of_week, "time_ist": schedule.time_ist, "slack_enabled": schedule.slack_enabled, "last_run_date": schedule.last_run_date, "timezone": "Asia/Kolkata"}

DEMO_SIGNALS = [
    Signal(id="sig-001", competitor="NovaTest", category="New AI capability", title="Announced guided AI test planning", first_detected=date(2026, 7, 30), confidence=92, evidence_status="Confirmed by official announcement"),
    Signal(id="sig-002", competitor="VerityQA", category="New ERP support", title="Added synthetic Workday coverage", first_detected=date(2026, 7, 27), confidence=84, evidence_status="Confirmed by official documentation"),
]

@app.get("/health", response_model=Health, tags=["system"])
def health() -> Health:
    return Health()

@app.get("/api/v1/signals", response_model=list[Signal], tags=["signals"])
def list_signals() -> list[Signal]:
    return DEMO_SIGNALS

@app.get("/api/v1/competitors", tags=["competitors"])
def list_competitors() -> list[dict[str, str]]:
    return [{"name": "NovaTest", "category": "AI-native competitor", "verification_status": "synthetic demo"}, {"name": "VerityQA", "category": "ERP specialist", "verification_status": "synthetic demo"}]

@app.get("/api/v1/brief", tags=["intelligence"])
def daily_brief() -> dict[str, object]:
    return {"mode": "synthetic-demo", "date_range": "2026-07-21 to 2026-08-01", "summary": "Two evidence-backed synthetic changes require PM review.", "citations": ["sig-001", "sig-002"]}

@app.post("/api/v1/claim-lens", tags=["intelligence"])
def claim_lens(text: str, documented: bool = False, implementation_evidence: bool = False) -> dict[str, str]:
    return classify_claim(text, documented, implementation_evidence)

@app.get("/api/v1/scores/example", tags=["intelligence"])
def scores_example() -> dict[str, object]:
    return {"strategic_importance": importance_score(90, 90, 70, 80, 80, 95), "threat": weighted_score({"capability_overlap": 80, "evidence": 90, "urgency": 75}), "opportunity": weighted_score({"customer_pain": 80, "alignment": 90, "differentiation": 85})}

@app.get("/api/v1/intelligence/today", tags=["intelligence"])
def get_today_intelligence() -> dict[str, object]:
    """Verified current signals with separate facts, inference, and citations."""
    return today_summary()

@app.get("/api/v1/intelligence/signals", response_model=list[EvidenceSignal], tags=["intelligence"])
def get_verified_intelligence_signals() -> list[EvidenceSignal]:
    return today_summary()["signals"]  # type: ignore[return-value]

@app.get("/api/v1/intelligence/competitive-analysis", tags=["intelligence"])
async def get_competitive_analysis(range_days: int = 90) -> dict[str, object]:
    """Evidence-grounded analysis; OpenAI is optional and always server-side."""
    if range_days not in {7, 30, 90}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="range_days must be 7, 30, or 90")
    return await analyze_competitors(range_days)

@app.get("/api/v1/automation/schedule", tags=["automation"])
def read_automation_schedule() -> dict[str, object]:
    return schedule_payload(get_schedule())

@app.put("/api/v1/automation/schedule", tags=["automation"])
async def save_automation_schedule(payload: ScheduleInput, _: str = Header(default=None, alias="Authorization")) -> dict[str, object]:
    await require_owner(_)
    return schedule_payload(update_schedule(payload.frequency, payload.day_of_week, payload.time_ist, payload.slack_enabled))

@app.post("/api/v1/automation/run", tags=["automation"])
async def run_automation_now(_: str = Header(default=None, alias="Authorization")) -> dict[str, object]:
    await require_owner(_)
    result = await run_daily_collection(send_slack=get_schedule().slack_enabled)
    mark_collected()
    return result

def require_scheduler_token(x_scheduler_token: str | None) -> None:
    expected = os.getenv("AUTOMATION_SCHEDULER_TOKEN", "") or os.getenv("SCHEDULER_TOKEN", "")
    if not expected or not x_scheduler_token or not hmac.compare_digest(expected, x_scheduler_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

@app.post("/api/v1/admin/notifications/teams/test", status_code=status.HTTP_204_NO_CONTENT, tags=["notifications"])
async def send_teams_test_notification(x_scheduler_token: str | None = Header(default=None)) -> None:
    """Protected diagnostic only; cannot be invoked by public dashboard visitors."""
    require_scheduler_token(x_scheduler_token)
    delivered = await post_teams_notification("TestOrbit delivery check", "A protected TestOrbit Teams webhook test was requested.", ["TestOrbit"])
    if not delivered:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Teams webhook is not configured")

@app.post("/api/v1/admin/notifications/slack/test", status_code=status.HTTP_204_NO_CONTENT, tags=["notifications"])
async def send_slack_test_notification(x_scheduler_token: str | None = Header(default=None)) -> None:
    """Protected diagnostic only; Slack webhook remains server-side."""
    require_scheduler_token(x_scheduler_token)
    delivered = await post_slack_notification("TestOrbit delivery check", "A protected TestOrbit Slack webhook test was requested.", ["TestOrbit"])
    if not delivered:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Slack webhook is not configured")

@app.post("/api/v1/admin/collect/daily", tags=["collection"])
async def collect_daily_changes(x_scheduler_token: str | None = Header(default=None)) -> dict[str, object]:
    """Protected daily collection and digest; only configured public sources are visited."""
    require_scheduler_token(x_scheduler_token)
    return await run_daily_collection(send_slack=True)

@app.post("/api/v1/admin/collect/scheduled", tags=["collection"])
async def collect_scheduled_changes(force: bool = False, authorization: str | None = Header(default=None, alias="Authorization")) -> dict[str, object]:
    verify_scheduler_oidc(authorization)
    due, schedule = collection_due()
    if not due and not force:
        return {"ran": False, "reason": "Not due", "schedule": schedule_payload(schedule)}
    result = await run_daily_collection(send_slack=schedule.slack_enabled)
    mark_collected()
    return {"ran": True, **result}
