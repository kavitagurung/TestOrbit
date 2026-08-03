from datetime import date
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .intelligence import classify_claim, importance_score, weighted_score
from .live_intelligence import EvidenceSignal, today_summary

app = FastAPI(title="TestOrbit API", version="0.1.0", description="Synthetic demo API. No confidential data.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://kavitagurung.github.io", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

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
