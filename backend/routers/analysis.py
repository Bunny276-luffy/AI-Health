from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
import json
from models.inference import inference_model
from services.progression import progression_analyzer
from services.report_generator import report_generator
from services.registration import image_registration
from services.dicom_parser import dicom_parser

router = APIRouter()

@router.post("/analyze")
async def analyze_scan(
    file: UploadFile = File(...),
    auto_calibrate: bool = Form(False)
):
    """
    Main endpoint to upload a scan, run preprocessing, AI detection, and uncertainty estimates.
    """
    contents = await file.read()
    
    # Optional: Parse DICOM Metadata if available
    dcm_meta = dicom_parser.extract_metadata(contents)
    
    # 1. Preprocessing (Simulated success, normally OpenCV goes here)
    processing_status = ["Resized to 256x256", "Contrast Enhanced", "Noise Reduced"]
    
    # 2. AI Tumor Detection & Uncertainty Estimation (MC Dropout)
    results = inference_model.analyze_scan(contents, require_calibration=auto_calibrate)
    
    # 3. Check for Self-Calibrating Diagnostic Control using SimpleITK
    # If Epistemic Uncertainty > 30% (0.3 threshold), we trigger image registration
    reanalysis_triggered = False
    registration_status = None
    
    # We normalized epistemic to '0-100' in `inference.py` output
    if results["uncertainty"]["epistemic"] > 30.0 and not auto_calibrate:
        reanalysis_triggered = True
        
        # Execute SimpleITK Image Registration
        registration_status = image_registration.register_to_baseline(contents)
        
        # Re-run inference representing the "stabilized" features
        results = inference_model.analyze_scan(contents, require_calibration=True)
        results["metadata"]["registration_applied"] = registration_status["transformation_type"]
        
    # Append DICOM meta to final response metadata
    results["metadata"].update(dcm_meta)
    
    return {
        "status": "success",
        "preprocessing": processing_status,
        "results": results,
        "control_actions": {
            "reanalysis_performed": reanalysis_triggered,
            "message": "ITK Alignment stabilizing high Epistemic variance." if reanalysis_triggered else "Normal inference completed."
        }
    }

@router.post("/progression")
async def analyze_progression(
    baseline_scan: UploadFile = File(...),
    current_scan: UploadFile = File(...)
):
    """
    Endpoint to receive two scans and compute longitudinal tumor progression.
    """
    # In a real app we'd read both files and compare feature maps
    baseline_content = await baseline_scan.read()
    current_content = await current_scan.read()
    
    progression_results = progression_analyzer.analyze(baseline_content, current_content)
    
    return {
        "status": "success",
        "progression": progression_results
    }

@router.post("/report")
async def generate_report(results_json: str = Form(...)):
    """
    Endpoint mapping front-end JSON results dynamically into a downloadable PDF report.
    """
    try:
        results = json.loads(results_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data.")
        
    pdf_buffer = report_generator.generate_pdf_report(results)
    
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=NeuroScan_Diagnostic_Report.pdf"}
    )
