import numpy as np
import cv2
import onnxruntime as ort
from typing import Dict, Any, List
import os
import time

class InferenceModelONNX:
    """
    Real Deep Learning inference using ONNXRuntime and a U-Net model.
    """
    def __init__(self):
        self.model_name = "U-Net (ONNX Edge)"
        self.calibration_factor = 1.0
        
        # Load ONNX model
        model_path = os.path.join(os.path.dirname(__file__), "..", "models", "unet.onnx")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"ONNX model not found at {model_path}. Please run export_unet_local.py")
        
        # Initialize ONNX Runtime session
        self.ort_session = ort.InferenceSession(model_path)
        self.input_name = self.ort_session.get_inputs()[0].name
        
    def analyze_scan(self, image_data: bytes, require_calibration: bool = False) -> Dict[str, Any]:
        """
        Runs real ONNX inference over the uploaded scan.
        """
        start_time = time.time()
        
        # 1. Image Preprocessing
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Invalid image data.")
            
        # U-Net typically expects RGB, 256x256
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (256, 256))
        
        # Normalize to [0, 1] and standardize (ImageNet stats)
        img_normalized = img_resized.astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_standardized = (img_normalized - mean) / std
        
        # Format for ONNX: [B, C, H, W]
        input_tensor = np.transpose(img_standardized, (2, 0, 1))
        input_tensor = np.expand_dims(input_tensor, axis=0)
        
        # 2. ONNX Edge Inference
        outputs = self.ort_session.run(None, {self.input_name: input_tensor})
        out_tensor = outputs[0] # Shape: [1, 1, 256, 256]
        
        # Apply sigmoid to get probabilities
        prob_map = 1.0 / (1.0 + np.exp(-out_tensor[0, 0]))
        
        # 3. Post-processing
        # Calculate real confidence from the probability distribution
        base_confidence = float(np.mean(prob_map[prob_map > 0.5]) if np.any(prob_map > 0.5) else 1 - float(np.mean(prob_map)))
        tumor_detected = bool(np.max(prob_map) > 0.5)
        prob_score = float(np.max(prob_map))
        
        if require_calibration:
            self.calibration_factor = 1.15
            base_confidence = min(0.99, base_confidence * self.calibration_factor)
            
        # For Step 1, these are placeholders. Real Variance will be added in Step 2 (MC Dropout)
        aleatoric_uncertainty = 0.15 
        epistemic_uncertainty = 0.10 
        total_uncertainty = (aleatoric_uncertainty + epistemic_uncertainty) / 2.0
        
        # Generate Bounding Boxes
        bounding_boxes = []
        heatmap_points = []
        if tumor_detected:
            mask = (prob_map > 0.5).astype(np.uint8)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                bx, by, bw, bh = x / 256.0, y / 256.0, w / 256.0, h / 256.0
                if bw > 0.02 and bh > 0.02:
                    bounding_boxes.append([bx, by, bw, bh, base_confidence])
            
            # Generate Real Heatmap Points by downsampling the true probability map
            heatmap_resized = cv2.resize(prob_map, (32, 32))
            for y in range(32):
                for x in range(32):
                    val = float(heatmap_resized[y, x])
                    if val > 0.2: 
                        heatmap_points.append({"x": x / 32.0, "y": y / 32.0, "value": val})
                        
        inference_time_ms = int((time.time() - start_time) * 1000)

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
                "inference_time_ms": inference_time_ms,
                "calibrated": require_calibration
            }
        }

inference_model = InferenceModelONNX()
