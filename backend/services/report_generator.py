import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from typing import Dict, Any

class ReportGenerator:
    """
    Generates PDF diagnostic reports for the uncertainty-aware tumor detection system.
    """
    
    def generate_pdf_report(self, results: Dict[str, Any]) -> io.BytesIO:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Header
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, "NeuroScan AI - Diagnostic Report")
        
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, "Uncertainty-Aware Tumor Detection Pipeline")
        
        c.line(50, height - 80, width - 50, height - 80)
        
        # Section 1: Prediction
        pred = results.get("prediction", {})
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 120, "1. Inference Results")
        
        c.setFont("Helvetica", 12)
        has_tumor = pred.get("has_tumor", False)
        status_text = "Anomalous Lesion Detected" if has_tumor else "No Significant Anomalies Detected"
        status_color = colors.red if has_tumor else colors.green
        
        c.setFillColor(status_color)
        c.drawString(70, height - 140, f"Diagnostic Finding: {status_text}")
        
        c.setFillColor(colors.black)
        c.drawString(70, height - 160, f"Tumor Probability: {pred.get('tumor_probability', 0)}%")
        c.drawString(70, height - 180, f"Model Confidence: {pred.get('confidence_score', 0)}%")
        
        # Section 2: Uncertainty
        uncert = results.get("uncertainty", {})
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 220, "2. Uncertainty Estimation")
        
        c.setFont("Helvetica", 12)
        c.drawString(70, height - 240, f"Total Uncertainty Level: {uncert.get('total', 0)}%")
        c.drawString(70, height - 260, f"Aleatoric (Data Noise): {uncert.get('aleatoric', 0)}%")
        c.drawString(70, height - 280, f"Epistemic (Model Knowledge): {uncert.get('epistemic', 0)}%")
        
        if uncert.get("is_high_uncertainty"):
            c.setFillColor(colors.orange)
            c.drawString(70, height - 300, "WARNING: High uncertainty detected. Clinical review mandated.")
            c.setFillColor(colors.black)
            
        # Section 3: Metadata
        meta = results.get("metadata", {})
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 340, "3. System Metrics")
        
        c.setFont("Helvetica", 12)
        c.drawString(70, height - 360, f"Inference Engine: {meta.get('model_used', 'N/A')}")
        c.drawString(70, height - 380, f"Processing Time: {meta.get('inference_time_ms', 0)} ms (Edge Optimized)")
        c.drawString(70, height - 400, f"Self-Calibration Triggered: {'Yes' if meta.get('calibrated') else 'No'}")
        
        # Footer
        c.setFont("Helvetica-Oblique", 9)
        c.setStrokeColor(colors.gray)
        c.line(50, 50, width - 50, 50)
        c.drawString(50, 35, "Generated automatically by NeuroScan AI. This is a primary screening tool, not a final clinical diagnosis.")
        
        c.showPage()
        c.save()
        
        buffer.seek(0)
        return buffer

report_generator = ReportGenerator()
