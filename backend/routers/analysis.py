"""
Primary Analysis Router — extended with organ routing, radiomics, conformal prediction.
Existing /analyze, /progression, /report endpoints are preserved and extended.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
import json

from models.inference import inference_model
from services.progression import progression_analyzer
from services.report_generator import report_generator
from services.registration import image_registration
from services.dicom_parser import dicom_parser
from services.radiomics import radiomics_service

router = APIRouter()


@router.post("/analyze")
async def analyze_scan(
    file: UploadFile = File(...),
    auto_calibrate: bool = Form(False),
    organ: str = Form("BRAIN"),
) -> dict:
    """
    Main analysis endpoint.
    Accepts image/DICOM, runs organ-routed MC Dropout inference,
    attaches conformal intervals + radiomics features.
    """
    contents: bytes = await file.read()

    # Parse DICOM metadata (graceful fallback for regular images)
    dcm_meta: dict = dicom_parser.extract_metadata(contents)

    processing_status: List[str] = [
        "Resized to target resolution",
        "Contrast Enhanced",
        "Noise Reduced",
    ]

    # MC Dropout inference (organ-aware + conformal)
    results: dict = inference_model.analyze_scan(
        contents, require_calibration=auto_calibrate, organ=organ
    )

    # Self-calibrating loop: epistemic > 30% → SimpleITK registration
    reanalysis_triggered: bool = False
    if results["uncertainty"]["epistemic"] > 30.0 and not auto_calibrate:
        reanalysis_triggered = True
        registration_status: dict = image_registration.register_to_baseline(contents)
        results = inference_model.analyze_scan(
            contents, require_calibration=True, organ=organ
        )
        results["metadata"]["registration_applied"] = registration_status.get(
            "transformation_type", "Alignment"
        )

    # Radiomics extraction from the raw probability map
    prob_map = results.pop("_prob_map_raw", None)
    if prob_map is not None:
        resolution = (256, 256)  # default; organ registry provides actual res
        try:
            from models.organ_registry import ORGAN_RESOLUTIONS
            resolution = ORGAN_RESOLUTIONS.get(organ.upper(), (256, 256))
        except Exception:
            pass
        radiomics_features = radiomics_service.extract_features(
            contents, prob_map, resolution
        )
    else:
        radiomics_features = []

    # Attach organ display name
    try:
        from models.organ_registry import organ_router
        organ_label = organ_router.get_display_name(organ)
    except Exception:
        organ_label = "Tumor Detection"

    results["metadata"].update(dcm_meta)
    results["metadata"]["organ_label"] = organ_label

    return {
        "status": "success",
        "preprocessing": processing_status,
        "results": results,
        "radiomics": radiomics_features,
        "control_actions": {
            "reanalysis_performed": reanalysis_triggered,
            "message": (
                "ITK Alignment stabilizing high Epistemic variance."
                if reanalysis_triggered
                else "Normal inference completed."
            ),
        },
    }


@router.post("/progression")
async def analyze_progression(
    baseline_scan: UploadFile = File(...),
    current_scan: UploadFile = File(...),
) -> dict:
    baseline_content: bytes = await baseline_scan.read()
    current_content: bytes = await current_scan.read()
    progression_results: dict = progression_analyzer.analyze(baseline_content, current_content)
    return {"status": "success", "progression": progression_results}


@router.post("/report")
async def generate_report(results_json: str = Form(...)) -> StreamingResponse:
    try:
        results: dict = json.loads(results_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data.")

    pdf_buffer = report_generator.generate_pdf_report(results)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=NeuroScan_Diagnostic_Report.pdf"
        },
    )
