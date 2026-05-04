"""
Visual Question Answering (VQA) Router
Grounds an LLM strictly in the numeric scan context — no hallucination beyond provided data.
"""
import os
from typing import Any, Dict, List

import anthropic
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field


router = APIRouter()

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class BoundingBox(BaseModel):
    x: float
    y: float
    w: float
    h: float
    confidence: float


class DicomMetadata(BaseModel):
    patient_age: str = "Unknown"
    modality: str = "Unknown"
    slice_thickness: str = "Unknown"
    dicom_valid: bool = False


class ScanContext(BaseModel):
    tumor_probability: float = Field(..., ge=0, le=100)
    epistemic_uncertainty: float = Field(..., ge=0, le=100)
    aleatoric_uncertainty: float = Field(..., ge=0, le=100)
    total_uncertainty: float = Field(..., ge=0, le=100)
    has_tumor: bool
    confidence_score: float = Field(..., ge=0, le=100)
    bounding_boxes: List[List[float]] = []
    dicom_metadata: DicomMetadata = Field(default_factory=DicomMetadata)
    organ: str = "BRAIN"


class VQARequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    scan_context: ScanContext


class VQAResponse(BaseModel):
    answer: str
    confidence: str
    disclaimer: str


# ---------------------------------------------------------------------------
# System Prompt Builder
# ---------------------------------------------------------------------------

def _build_system_prompt(ctx: ScanContext) -> str:
    boxes_text = (
        f"{len(ctx.bounding_boxes)} region(s) detected"
        if ctx.bounding_boxes
        else "No bounding boxes detected"
    )
    return f"""You are NeuroScan's clinical AI assistant. You answer clinician questions
STRICTLY based on the numerical scan context provided below.
You MUST NOT invent, extrapolate, or suggest clinical conclusions beyond what the data states.
If you cannot answer from the data, say: "The scan data does not provide enough information to answer that."

=== SCAN CONTEXT ===
Organ Scanned        : {ctx.organ}
Tumor Detected       : {"YES" if ctx.has_tumor else "NO"}
Tumor Probability    : {ctx.tumor_probability:.1f}%
Model Confidence     : {ctx.confidence_score:.1f}%
Epistemic Uncertainty: {ctx.epistemic_uncertainty:.1f}%  (model knowledge gap)
Aleatoric Uncertainty: {ctx.aleatoric_uncertainty:.1f}%  (data/image noise)
Total Uncertainty    : {ctx.total_uncertainty:.1f}%
Lesion Regions       : {boxes_text}
Patient Age          : {ctx.dicom_metadata.patient_age}
Modality             : {ctx.dicom_metadata.modality}
Slice Thickness      : {ctx.dicom_metadata.slice_thickness}
=== END CONTEXT ===

Rules:
1. Answer concisely in 2-4 sentences.
2. Always end with uncertainty caveats if epistemic > 25%.
3. Never recommend treatment — only describe what the scan data indicates.
4. Use plain English, not jargon, unless the clinician's question uses jargon."""


# ---------------------------------------------------------------------------
# Streaming Endpoint
# ---------------------------------------------------------------------------

@router.post("/vqa/stream")
async def vqa_stream(request: VQARequest) -> StreamingResponse:
    """
    Streams the LLM's answer token-by-token using Server-Sent Events.
    The LLM is grounded strictly in the numeric scan_context.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    def generate():
        # Fallback simulated response if no real API key is provided
        if not api_key or api_key == "your_anthropic_api_key_here":
            import asyncio
            import time
            
            # Simulated clinically-grounded response based on the context
            ctx = request.scan_context
            simulated_response = (
                f"**[SIMULATED AI RESPONSE - NO API KEY DETECTED]**\n\n"
                f"Based on the analysis of this {ctx.organ} scan, the MC Dropout ensemble "
                f"has detected a lesion with a probability of {ctx.tumor_probability:.1f}%. "
                f"The epistemic uncertainty is {ctx.epistemic_uncertainty:.1f}%, which indicates "
                f"the model's knowledge gap is {'high' if ctx.epistemic_uncertainty > 20 else 'low'}, "
                f"and the aleatoric uncertainty (data noise) is {ctx.aleatoric_uncertainty:.1f}%. "
                f"With a {ctx.confidence_score:.1f}% confidence score, clinical correlation is strongly advised."
            )
            
            words = simulated_response.split(" ")
            for word in words:
                yield f"data: {json.dumps({'chunk': word + ' '})}\n\n"
                time.sleep(0.05)
            yield "data: [DONE]\n\n"
            return

        # Real Anthropic call
        try:
            client = anthropic.Anthropic(api_key=api_key)
            system_prompt = _build_system_prompt(request.scan_context)
            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=512,
                system=system_prompt,
                messages=[{"role": "user", "content": request.question}],
            ) as stream:
                for text in stream.text_stream:
                    # JSON encode the chunk so the frontend parser works smoothly
                    yield f"data: {json.dumps({'chunk': text})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'chunk': f'[ERROR] {str(e)}'})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Non-streaming fallback (for testing / PDF reports)
# ---------------------------------------------------------------------------

@router.post("/vqa", response_model=VQAResponse)
async def vqa_sync(request: VQARequest) -> VQAResponse:
    """
    Non-streaming VQA endpoint. Returns the complete answer in one response.
    Useful for PDF report generation and automated pipelines.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return VQAResponse(
            answer="VQA unavailable: ANTHROPIC_API_KEY not configured.",
            confidence="N/A",
            disclaimer=(
                "AI-generated response — not a clinical diagnosis. "
                "Always consult a qualified radiologist."
            ),
        )

    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = _build_system_prompt(request.scan_context)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        system=system_prompt,
        messages=[{"role": "user", "content": request.question}],
    )

    answer_text: str = message.content[0].text  # type: ignore[index]

    uncertainty = request.scan_context.epistemic_uncertainty
    confidence_label = (
        "Low — high epistemic uncertainty" if uncertainty > 30
        else "Moderate" if uncertainty > 15
        else "High"
    )

    return VQAResponse(
        answer=answer_text,
        confidence=confidence_label,
        disclaimer=(
            "AI-generated response grounded in scan metrics only — "
            "not a clinical diagnosis. Always consult a qualified radiologist."
        ),
    )
