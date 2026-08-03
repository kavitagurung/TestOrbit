"""Gemini boundary: validated structured outputs with a deterministic fallback."""
from pydantic import BaseModel, Field
from .intelligence import safe_ai_input

class AIInterpretation(BaseModel):
    summary: str = Field(max_length=600)
    suggested_capabilities: list[str] = Field(default_factory=list, max_length=10)
    availability: str

def fallback_interpretation(source_text: str) -> AIInterpretation:
    clean = safe_ai_input(source_text)
    return AIInterpretation(summary=f"AI interpretation unavailable. Rule-based summary retained ({len(clean)} bounded characters prepared).", availability="unavailable")

def validate_ai_response(payload: dict) -> AIInterpretation:
    return AIInterpretation.model_validate(payload)

