"""
Temporal Scan Comparison Router
Accepts two scan uploads, runs independent inference on each,
and computes progression metrics including Volume Doubling Time (VDT).
"""
import math
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

import numpy as np
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from pydantic import BaseModel

from models.inference import inference_model

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic Response Models
# ---------------------------------------------------------------------------

class HeatmapPoint(BaseModel):
    x: float
    y: float
    value: float


class ComparisonMetrics(BaseModel):
    probability_delta: float
    volume_delta_percent: float
    uncertainty_delta: float
    vdt_days: Optional[float]
    vdt_interpretation: Optional[str]
    severity: str  # "stable" | "moderate" | "critical"


class CompareResponse(BaseModel):
    status: str
    scan_a: Dict[str, Any]
    scan_b: Dict[str, Any]
    metrics: ComparisonMetrics


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _estimate_volume(bounding_boxes: List[List[float]]) -> float:
    """
    Estimates relative 2-D area (proxy for volume) from bounding boxes.
    Each box is [x, y, w, h, confidence] in normalised [0..1] coordinates.
    """
    if not bounding_boxes:
        return 0.0
    total_area = sum(box[2] * box[3] for box in bounding_boxes)
    return float(total_area)


def _compute_vdt(
    volume_a: float,
    volume_b: float,
    date_a: Optional[str],
    date_b: Optional[str],
) -> tuple[Optional[float], Optional[str]]:
    """
    Computes Volume Doubling Time (days) using the Schwartz formula:
        VDT = T * ln(2) / ln(Vb / Va)
    Returns (vdt_days, interpretation_string).
    """
    if not date_a or not date_b:
        return None, None
    if volume_a <= 0 or volume_b <= 0 or volume_b <= volume_a:
        return None, None
    try:
        fmt = "%Y-%m-%d"
        t_a = datetime.strptime(date_a, fmt).replace(tzinfo=timezone.utc)
        t_b = datetime.strptime(date_b, fmt).replace(tzinfo=timezone.utc)
        T = (t_b - t_a).days
        if T <= 0:
            return None, None
        vdt = T * math.log(2) / math.log(volume_b / volume_a)
        vdt = round(vdt, 1)

        if vdt < 100:
            interp = f"Fast growth — VDT {vdt} days. Urgent clinical review recommended."
        elif vdt < 300:
            interp = f"Moderate growth — VDT {vdt} days. Close monitoring advised."
        elif vdt < 600:
            interp = f"Slow growth — VDT {vdt} days. Routine follow-up sufficient."
        else:
            interp = f"Very slow or indolent — VDT {vdt} days. Low immediate risk."

        return vdt, interp
    except ValueError:
        return None, None


def _severity_label(delta: float) -> str:
    abs_d = abs(delta)
    if abs_d < 5:
        return "stable"
    if abs_d < 20:
        return "moderate"
    return "critical"


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/compare", response_model=CompareResponse)
async def compare_scans(
    scan_a: UploadFile = File(..., description="Baseline scan"),
    scan_b: UploadFile = File(..., description="Follow-up scan"),
    timestamp_a: str = Form("", description="Baseline date YYYY-MM-DD (optional)"),
    timestamp_b: str = Form("", description="Follow-up date YYYY-MM-DD (optional)"),
) -> CompareResponse:
    """
    Runs full MC Dropout inference on both scans independently,
    then computes temporal progression metrics.
    """
    bytes_a = await scan_a.read()
    bytes_b = await scan_b.read()

    if not bytes_a or not bytes_b:
        raise HTTPException(status_code=400, detail="Both scan files must be non-empty.")

    # Independent inference on each scan
    result_a = inference_model.analyze_scan(bytes_a, require_calibration=False)
    result_b = inference_model.analyze_scan(bytes_b, require_calibration=False)

    # Extract key scalars
    prob_a = result_a["prediction"]["tumor_probability"]
    prob_b = result_b["prediction"]["tumor_probability"]

    unc_a = result_a["uncertainty"]["total"]
    unc_b = result_b["uncertainty"]["total"]

    vol_a = _estimate_volume(result_a["visualizations"]["bounding_boxes"])
    vol_b = _estimate_volume(result_b["visualizations"]["bounding_boxes"])

    probability_delta = round(prob_b - prob_a, 2)
    volume_delta_percent = (
        round(((vol_b - vol_a) / vol_a) * 100, 2) if vol_a > 0 else 0.0
    )
    uncertainty_delta = round(unc_b - unc_a, 2)

    vdt_days, vdt_interpretation = _compute_vdt(
        vol_a, vol_b,
        timestamp_a or None,
        timestamp_b or None,
    )

    metrics = ComparisonMetrics(
        probability_delta=probability_delta,
        volume_delta_percent=volume_delta_percent,
        uncertainty_delta=uncertainty_delta,
        vdt_days=vdt_days,
        vdt_interpretation=vdt_interpretation,
        severity=_severity_label(probability_delta),
    )

    return CompareResponse(
        status="success",
        scan_a={
            "prediction": result_a["prediction"],
            "uncertainty": result_a["uncertainty"],
            "heatmap_data": result_a["visualizations"]["heatmap_data"],
            "bounding_boxes": result_a["visualizations"]["bounding_boxes"],
            "estimated_volume": round(vol_a, 5),
        },
        scan_b={
            "prediction": result_b["prediction"],
            "uncertainty": result_b["uncertainty"],
            "heatmap_data": result_b["visualizations"]["heatmap_data"],
            "bounding_boxes": result_b["visualizations"]["bounding_boxes"],
            "estimated_volume": round(vol_b, 5),
        },
        metrics=metrics,
    )
