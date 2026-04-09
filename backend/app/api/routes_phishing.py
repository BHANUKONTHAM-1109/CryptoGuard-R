"""
CryptoGuard-R - Phishing Detection API
"""

from fastapi import APIRouter, HTTPException

from pydantic import BaseModel, Field

from app.ai.phishing_model import get_model, get_phishing_score

router = APIRouter(prefix="/api/phishing", tags=["phishing"])


class PhishingRequest(BaseModel):
    """Request body for phishing check."""

    message: str = Field(..., min_length=1, max_length=50000, description="Email or message text to analyze")


class PhishingResponse(BaseModel):
    """Response with phishing score."""

    score: float = Field(..., ge=0, le=1, description="Probability of phishing (0=legitimate, 1=phishing)")
    is_phishing: bool = Field(..., description="True if score >= 0.5")
    message: str = Field(..., description="Status message")
    is_safe: bool = Field(..., description="True if Semantic Filter clears it for physical safety")
    safety_reason: str = Field(..., description="Description of the safety filter result")


@router.post("/check", response_model=PhishingResponse)
def check_phishing(req: PhishingRequest) -> PhishingResponse:
    """Analyze message for phishing probability."""
    model = get_model()
    if model is None:
        raise HTTPException(status_code=503, detail="Phishing model not loaded; train model first")
    score = get_phishing_score(model, req.message)
    is_phishing = score >= 0.5
    
    from app.ai.semantic_safety import evaluate_safety
    is_safe, safety_reason = evaluate_safety(req.message)
    
    return PhishingResponse(
        score=round(score, 4),
        is_phishing=is_phishing,
        message="Phishing detected" if is_phishing else "Likely legitimate",
        is_safe=is_safe,
        safety_reason=safety_reason,
    )
