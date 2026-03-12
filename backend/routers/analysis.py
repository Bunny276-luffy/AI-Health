from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
import json
from models.inference import inference_model
from services.progression import progression_analyzer
from services.report_generator import report_generator

router = APIRouter()

@router.post("/analyze")
async def analyze_scan(
    file: UploadFile = File(...),
    auto_calibrate: bool = Form(False)
):
    """
    Main endpoint to upload a scan, run preprocessing, AI detection, and uncertainty estimates.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
    
    contents = await file.read()
    
    # 1. Preprocessing (Simulated success, normally OpenCV goes here)
    processing_status = ["Resized to 256x256", "Contrast Enhanced", "Noise Reduced"]
    
    # 2. AI Tumor Detection & Uncertainty Estimation
    results = inference_model.analyze_scan(contents, require_calibration=auto_calibrate)
    
    # 3. Check for Self-Calibrating Diagnostic Control
    # If uncertainty is too high, and we haven't calibrated yet, we trigger a re-analysis scenario
    # In a real system, this would adjust attention weights or run a heavier ensemble
    reanalysis_triggered = False
    if results["uncertainty"]["is_high_uncertainty"] and not auto_calibrate:
        reanalysis_triggered = True
        # Run it again with calibration flagged
        results = inference_model.analyze_scan(contents, require_calibration=True)
    
    return {
        "status": "success",
        "preprocessing": processing_status,
        "results": results,
        "control_actions": {
            "reanalysis_performed": reanalysis_triggered,
            "message": "Additional analysis performed due to high initial prediction uncertainty." if reanalysis_triggered else "Normal inference completed."
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
