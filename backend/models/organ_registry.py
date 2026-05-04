"""
Multi-Organ Model Registry and Router
Handles ONNX session loading per organ type with organ-specific preprocessing.
"""
from enum import Enum
from typing import Dict, Optional, Tuple
import os
import numpy as np
import cv2
import onnxruntime as ort


class OrganType(str, Enum):
    BRAIN = "BRAIN"
    LUNG = "LUNG"
    LIVER = "LIVER"
    PROSTATE = "PROSTATE"


# Organ-specific input resolutions (H, W)
ORGAN_RESOLUTIONS: Dict[str, Tuple[int, int]] = {
    OrganType.BRAIN: (256, 256),
    OrganType.LUNG: (512, 512),
    OrganType.LIVER: (256, 256),
    OrganType.PROSTATE: (320, 320),
}

# Organ display names for API/frontend
ORGAN_DISPLAY_NAMES: Dict[str, str] = {
    OrganType.BRAIN: "Brain Tumor Detection",
    OrganType.LUNG: "Lung Nodule Detection",
    OrganType.LIVER: "Liver Lesion Detection",
    OrganType.PROSTATE: "Prostate Cancer Detection",
}


def _get_model_path(organ: str) -> str:
    """Resolves .onnx file path for a given organ. Falls back to brain model if organ-specific not found."""
    models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    organ_model_map: Dict[str, str] = {
        OrganType.BRAIN: "unet.onnx",
        OrganType.LUNG: "unet_lung.onnx",
        OrganType.LIVER: "unet_liver.onnx",
        OrganType.PROSTATE: "unet_prostate.onnx",
    }
    filename = organ_model_map.get(organ, "unet.onnx")
    path = os.path.abspath(os.path.join(models_dir, filename))

    # Fallback: if organ-specific model doesn't exist, use the base brain U-Net
    if not os.path.exists(path):
        path = os.path.abspath(os.path.join(models_dir, "unet.onnx"))

    return path


class OrganRouter:
    """
    Manages ONNX inference sessions keyed by organ type.
    Sessions are loaded lazily on first use and cached in memory.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, ort.InferenceSession] = {}

    def get_session(self, organ: str) -> ort.InferenceSession:
        """Returns a cached or newly loaded ONNX session for the requested organ."""
        organ_key = organ.upper()
        if organ_key not in self._sessions:
            model_path = _get_model_path(organ_key)
            if not os.path.exists(model_path):
                raise FileNotFoundError(
                    f"No ONNX model found for organ '{organ_key}'. "
                    f"Expected at: {model_path}"
                )
            self._sessions[organ_key] = ort.InferenceSession(model_path)
        return self._sessions[organ_key]

    def preprocess(self, image_data: bytes, organ: str) -> Tuple[np.ndarray, Tuple[int, int]]:
        """
        Organ-aware image preprocessing.
        Returns the preprocessed input tensor and the (H, W) used for this organ.
        """
        organ_key = organ.upper()
        target_h, target_w = ORGAN_RESOLUTIONS.get(organ_key, (256, 256))

        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Cannot decode image bytes.")

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (target_w, target_h))

        img_normalized = img_resized.astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_std = (img_normalized - mean) / std

        # [B, C, H, W]
        tensor = np.expand_dims(np.transpose(img_std, (2, 0, 1)), axis=0)
        return tensor, (target_h, target_w)

    def get_display_name(self, organ: str) -> str:
        """Returns a human-readable detection mode name for the given organ."""
        return ORGAN_DISPLAY_NAMES.get(organ.upper(), "Tumor Detection")


# Singleton instance used across the application
organ_router = OrganRouter()
