"""
Conformal Prediction Layer
Wraps Monte Carlo Dropout ensemble outputs with statistically guaranteed
prediction intervals at 90% coverage using split conformal prediction.
"""
import os
import json
import numpy as np
from typing import List, Dict, Any


CALIBRATION_STORE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "models", "conformal_calibration.json"
)


class ConformalPredictor:
    """
    Split conformal predictor for binary tumor classification.

    Calibration:
        - Collect nonconformity scores: s_i = 1 - p_i  (for true-positive scans)
          on a held-out calibration set.
        - Store the (1 - alpha) quantile of those scores as the threshold q_hat.

    Inference:
        - For a new prediction p_new:
            lower = max(0, p_new - q_hat)
            upper = min(1, p_new + q_hat)
        - prediction_set lists class labels whose scores fall within interval.
    """

    def __init__(self, alpha: float = 0.10) -> None:
        """
        Args:
            alpha: significance level. alpha=0.10 → 90% coverage guarantee.
        """
        self.alpha = alpha
        self.coverage = 1.0 - alpha
        self.q_hat: float = 0.20  # sensible default before calibration

        self._try_load_calibration()

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------

    def calibrate(self, true_probs: List[float]) -> float:
        """
        Fit the conformal predictor on calibration probabilities
        (output of the MC Dropout ensemble on a labeled calibration set).

        Args:
            true_probs: list of predicted probabilities for the TRUE class label.
        Returns:
            The computed q_hat threshold.
        """
        scores = np.array([1.0 - p for p in true_probs], dtype=np.float64)
        n = len(scores)
        # Compute the ceil((n+1)(1-alpha))/n quantile
        level = np.ceil((n + 1) * (1.0 - self.alpha)) / n
        level = min(level, 1.0)
        self.q_hat = float(np.quantile(scores, level))
        self._save_calibration()
        return self.q_hat

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict(self, prob_score: float) -> Dict[str, Any]:
        """
        Wrap a scalar probability with a conformal prediction interval.

        Args:
            prob_score: mean probability from the 10-pass MC Dropout ensemble (0-1).
        Returns:
            Dict with lower_bound, upper_bound, coverage, prediction_set.
        """
        lower = float(max(0.0, prob_score - self.q_hat))
        upper = float(min(1.0, prob_score + self.q_hat))

        prediction_set: List[str] = []
        if lower <= 0.5 <= upper or upper < 0.5:
            prediction_set.append("NO_TUMOR")
        if lower > 0.5 or upper >= 0.5:
            prediction_set.append("TUMOR")

        return {
            "lower_bound": round(lower, 4),
            "upper_bound": round(upper, 4),
            "coverage": self.coverage,
            "q_hat": round(self.q_hat, 4),
            "prediction_set": prediction_set,
        }

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _save_calibration(self) -> None:
        os.makedirs(os.path.dirname(CALIBRATION_STORE_PATH), exist_ok=True)
        with open(CALIBRATION_STORE_PATH, "w") as f:
            json.dump({"q_hat": self.q_hat, "alpha": self.alpha}, f)

    def _try_load_calibration(self) -> None:
        if os.path.exists(CALIBRATION_STORE_PATH):
            with open(CALIBRATION_STORE_PATH, "r") as f:
                data = json.load(f)
            self.q_hat = data.get("q_hat", self.q_hat)
            self.alpha = data.get("alpha", self.alpha)
            self.coverage = 1.0 - self.alpha


# Singleton
conformal_predictor = ConformalPredictor()
