from typing import Dict, Any, List
import random
import math

class InferenceModelMock:
    """
    Simulates a PyTorch Deep Learning model inference for tumor detection.
    This generates realistic-looking mock data for demonstration purposes,
    including Aleatoric (data noise) and Epistemic (model knowledge) uncertainty.
    """
    
    def __init__(self):
        self.model_name = "ResNet50-Neuro-Ensemble-v2"
        self.calibration_factor = 1.0
        
    def analyze_scan(self, image_data: bytes, require_calibration: bool = False) -> Dict[str, Any]:
        """
        Simulates running the ensemble model over the scan.
        """
        # Simulate base confidence based on 'image quality' (randomized for mock)
        base_confidence = random.uniform(0.65, 0.99)
        
        if require_calibration:
            # Self-calibrating diagnostic control enhances confidence
            self.calibration_factor = 1.15
            base_confidence = min(0.99, base_confidence * self.calibration_factor)
        
        # Calculate simulated uncertainties
        # Aleatoric Uncertainty: Inherent data noise (e.g., poor scan quality, artifacts)
        aleatoric_raw = random.uniform(0.01, 0.4)
        aleatoric_uncertainty = aleatoric_raw * (1.0 if not require_calibration else 0.8)
        
        # Epistemic Uncertainty: Model ignorance (e.g., out-of-distribution sample)
        # Usually inversely proportional to confidence in this mock
        epistemic_raw = random.uniform(0.01, 1 - base_confidence)
        epistemic_uncertainty = epistemic_raw * (1.0 if not require_calibration else 0.5)
        
        total_uncertainty = (aleatoric_uncertainty + epistemic_uncertainty) / 2.0
        
        # Tumor Probability Map (Simulated as an overall percentage + heatmap data points)
        tumor_detected = base_confidence > 0.75
        prob_score = random.uniform(0.8, 0.99) if tumor_detected else random.uniform(0.05, 0.3)
        
        # Mocking bounding boxes if tumor detected
        bounding_boxes = []
        if tumor_detected:
            num_lesions = random.randint(1, 3)
            for _ in range(num_lesions):
                # Format: [x, y, width, height, confidence] relative to image (0-1)
                bx = random.uniform(0.2, 0.7)
                by = random.uniform(0.2, 0.7)
                bw = random.uniform(0.1, 0.3)
                bh = random.uniform(0.1, 0.3)
                bounding_boxes.append([bx, by, bw, bh, random.uniform(0.8, base_confidence)])
                
        # Generate heatmap points simulating the probability density
        heatmap_points = self._generate_heatmap_points(bounding_boxes)
                
        return {
            "prediction": {
                "has_tumor": tumor_detected,
                "tumor_probability": round(prob_score * 100, 2),
                "confidence_score": round(base_confidence * 100, 2)
            },
            "uncertainty": {
                "aleatoric": round(aleatoric_uncertainty * 100, 2),
                "epistemic": round(epistemic_uncertainty * 100, 2),
                "total": round(total_uncertainty * 100, 2),
                "is_high_uncertainty": total_uncertainty > 0.25
            },
            "visualizations": {
                "bounding_boxes": bounding_boxes,
                "heatmap_data": heatmap_points
            },
            "metadata": {
                "model_used": self.model_name,
                "inference_time_ms": random.randint(150, 450),  # Simulated Edge inference speed
                "calibrated": require_calibration
            }
        }
        
    def _generate_heatmap_points(self, bounding_boxes: List[List[float]]) -> List[Dict[str, float]]:
        """Generates random clusters of points representing high activation regions."""
        points = []
        for box in bounding_boxes:
            x, y, w, h, conf = box
            center_x = x + w/2
            center_y = y + h/2
            
            # Generate 50 points around this center
            for _ in range(50):
                px = random.gauss(center_x, w/3)
                py = random.gauss(center_y, h/3)
                intensity = max(0.1, random.gauss(conf, 0.2))
                if 0 <= px <= 1 and 0 <= py <= 1:
                    points.append({"x": px, "y": py, "value": intensity})
                    
        return points

inference_model = InferenceModelMock()
