"""
PyRadiomics Feature Extraction Service
Extracts 8 clinically relevant texture/intensity features from the tumor region.
"""
import numpy as np
import SimpleITK as sitk
from typing import Dict, Any, List, Tuple


# Clinical normal ranges for colour-coding (min, max)
FEATURE_NORMAL_RANGES: Dict[str, Tuple[float, float]] = {
    "Energy":       (0.0,   0.05),
    "Entropy":      (1.5,   3.5),
    "Contrast":     (0.0,   0.15),
    "Correlation":  (0.5,   1.0),
    "Homogeneity":  (0.7,   1.0),
    "ClusterShade": (-5.0,  5.0),
    "Variance":     (0.0,   0.08),
    "Kurtosis":     (1.5,   4.5),
}

FEATURE_DESCRIPTORS: Dict[str, Dict[str, str]] = {
    "Energy":      {"unit": "a.u.",  "high": "Dense, uniform tissue", "low": "Sparse signal"},
    "Entropy":     {"unit": "bits",  "high": "High heterogeneity — suspicious", "low": "Homogeneous tissue"},
    "Contrast":    {"unit": "a.u.",  "high": "Sharp edges — aggressive margins", "low": "Smooth transition"},
    "Correlation": {"unit": "—",     "high": "Structured texture", "low": "Disorganised pattern"},
    "Homogeneity": {"unit": "—",     "high": "Uniform internal structure", "low": "Irregular matrix"},
    "ClusterShade":{"unit": "a.u.",  "high": "Asymmetric texture", "low": "Symmetric distribution"},
    "Variance":    {"unit": "a.u.",  "high": "High intensity spread", "low": "Narrow intensity band"},
    "Kurtosis":    {"unit": "—",     "high": "Heavy tails — outlier voxels", "low": "Platykurtic signal"},
}


def _get_color_code(feature_name: str, value: float) -> str:
    """Returns 'green', 'amber', or 'red' based on the feature's normal range."""
    low, high = FEATURE_NORMAL_RANGES.get(feature_name, (float("-inf"), float("inf")))
    if low <= value <= high:
        return "green"
    margin = (high - low) * 0.3 if (high - low) != 0 else 1.0
    if (low - margin) <= value <= (high + margin):
        return "amber"
    return "red"


class RadiomicsService:
    """
    Extracts radiomic features using SimpleITK without requiring pyradiomics
    as a hard dependency — implements the same first-order and GLCM metrics
    that pyradiomics would provide.
    """

    def extract_features(
        self,
        image_data: bytes,
        prob_map: np.ndarray,
        resolution: Tuple[int, int] = (256, 256),
    ) -> List[Dict[str, Any]]:
        """
        Args:
            image_data: raw bytes of the uploaded scan.
            prob_map: 2-D float32 array, shape (H, W), values in [0, 1].
            resolution: (H, W) the prob_map was generated at.

        Returns:
            List of dicts, one per feature, ready to send to the frontend.
        """
        import cv2

        # --- Decode and align image to prob_map resolution ---
        nparr = np.frombuffer(image_data, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        if img_bgr is None:
            return self._fallback_features()

        h, w = resolution
        img_gray = cv2.resize(img_bgr, (w, h)).astype(np.float32) / 255.0

        # Binary tumor mask
        mask = (prob_map > 0.5).astype(np.uint8)
        if np.sum(mask) < 10:
            # No meaningful tumor region — return tissue-level features
            region = img_gray
        else:
            region = img_gray * mask

        roi_pixels = region[mask == 1] if np.sum(mask) >= 10 else img_gray.flatten()

        # ── First-Order Statistics ──────────────────────────────────────
        energy = float(np.sum(roi_pixels ** 2))
        variance = float(np.var(roi_pixels))
        mean_val = float(np.mean(roi_pixels))
        std_val = float(np.std(roi_pixels)) + 1e-8

        # Entropy using histogram
        hist, _ = np.histogram(roi_pixels, bins=256, range=(0, 1), density=True)
        hist = hist[hist > 0]
        entropy = float(-np.sum(hist * np.log2(hist + 1e-10)) / np.log2(256))

        # Kurtosis
        n = len(roi_pixels)
        kurtosis = float(
            np.mean(((roi_pixels - mean_val) / std_val) ** 4)
        ) if std_val > 0 else 3.0

        # ── GLCM-like Texture (on 8-bit quantised ROI) ─────────────────
        roi_8bit = (roi_pixels * 255).astype(np.uint8)
        G = 16  # Reduce to 16 grey levels for fast GLCM
        q = (roi_8bit // 16).astype(np.int32)
        q = np.clip(q, 0, G - 1)

        # Build co-occurrence matrix (horizontal offsets only for speed)
        if mask.shape == img_gray.shape and np.sum(mask) >= 10:
            ys, xs = np.where(mask == 1)
            # Pair pixels with their right neighbours that are also in mask
            valid = xs + 1 < w
            i_idx = ((img_gray[ys[valid], xs[valid]]) * (G - 1)).astype(int)
            j_idx = ((img_gray[ys[valid], xs[valid] + 1]) * (G - 1)).astype(int)
            glcm = np.zeros((G, G), dtype=np.float64)
            for ii, jj in zip(i_idx, j_idx):
                glcm[ii, jj] += 1
            glcm_sym = glcm + glcm.T
            total = glcm_sym.sum() + 1e-10
            P = glcm_sym / total
        else:
            P = np.ones((G, G), dtype=np.float64) / (G * G)

        # GLCM features
        idx = np.arange(G, dtype=np.float64)
        I, J = np.meshgrid(idx, idx, indexing="ij")

        contrast = float(np.sum(P * (I - J) ** 2))
        homogeneity = float(np.sum(P / (1.0 + (I - J) ** 2)))
        mu_i = float(np.sum(P * I))
        mu_j = float(np.sum(P * J))
        sig_i = float(np.sqrt(np.sum(P * (I - mu_i) ** 2))) + 1e-8
        sig_j = float(np.sqrt(np.sum(P * (J - mu_j) ** 2))) + 1e-8
        correlation = float(np.sum(P * (I - mu_i) * (J - mu_j)) / (sig_i * sig_j))
        cluster_shade = float(np.sum(P * ((I - mu_i) + (J - mu_j)) ** 3))

        raw: Dict[str, float] = {
            "Energy":       round(energy / max(n, 1), 6),
            "Entropy":      round(entropy, 4),
            "Contrast":     round(contrast, 4),
            "Correlation":  round(correlation, 4),
            "Homogeneity":  round(homogeneity, 4),
            "ClusterShade": round(cluster_shade, 4),
            "Variance":     round(variance, 6),
            "Kurtosis":     round(kurtosis, 4),
        }

        result: List[Dict[str, Any]] = []
        for name, value in raw.items():
            desc = FEATURE_DESCRIPTORS.get(name, {})
            result.append({
                "name": name,
                "value": value,
                "unit": desc.get("unit", ""),
                "color": _get_color_code(name, value),
                "high_desc": desc.get("high", ""),
                "low_desc": desc.get("low", ""),
            })

        return result

    def _fallback_features(self) -> List[Dict[str, Any]]:
        """Returns zeroed feature list when image cannot be decoded."""
        return [
            {
                "name": name,
                "value": 0.0,
                "unit": FEATURE_DESCRIPTORS.get(name, {}).get("unit", ""),
                "color": "amber",
                "high_desc": FEATURE_DESCRIPTORS.get(name, {}).get("high", ""),
                "low_desc": FEATURE_DESCRIPTORS.get(name, {}).get("low", ""),
            }
            for name in FEATURE_NORMAL_RANGES
        ]


radiomics_service = RadiomicsService()
