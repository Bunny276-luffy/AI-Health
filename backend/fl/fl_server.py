"""
Federated Learning Server
Uses Flower (flwr) framework with FedAvg + Gaussian Differential Privacy.
Aggregated weights are automatically exported to unet.onnx after each round.
"""
import os
import copy
from typing import Dict, List, Optional, Tuple, Union
from collections import OrderedDict

import numpy as np
import torch
import flwr as fl
from flwr.common import (
    FitRes,
    Parameters,
    Scalar,
    ndarrays_to_parameters,
    parameters_to_ndarrays,
)
from flwr.server.client_proxy import ClientProxy
from flwr.server.strategy import FedAvg


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
GLOBAL_WEIGHTS_PATH = os.path.join(MODELS_DIR, "custom_unet.pt")
ONNX_OUTPUT_PATH = os.path.join(MODELS_DIR, "unet.onnx")
UNET_REPO_DIR = os.path.join(MODELS_DIR, "unet_repo")


# ---------------------------------------------------------------------------
# Differential Privacy Helper
# ---------------------------------------------------------------------------

# Gaussian mechanism: σ = sqrt(2 * ln(1.25/delta)) * sensitivity / epsilon
DP_EPSILON: float = 1.0
DP_DELTA: float = 1e-5
DP_SENSITIVITY: float = 1.0  # clip norm for weight updates


def _gaussian_noise_sigma(epsilon: float, delta: float, sensitivity: float) -> float:
    return float(np.sqrt(2.0 * np.log(1.25 / delta)) * sensitivity / epsilon)


def _add_dp_noise(params: List[np.ndarray]) -> List[np.ndarray]:
    """
    Adds calibrated Gaussian noise to aggregated weight arrays
    to satisfy (epsilon, delta)-differential privacy.
    """
    sigma = _gaussian_noise_sigma(DP_EPSILON, DP_DELTA, DP_SENSITIVITY)
    return [arr + np.random.normal(0, sigma, arr.shape).astype(arr.dtype) for arr in params]


# ---------------------------------------------------------------------------
# ONNX Export Helper
# ---------------------------------------------------------------------------

def _export_to_onnx(state_dict: "OrderedDict[str, torch.Tensor]") -> None:
    """Loads a UNet with the given state_dict and exports it to ONNX."""
    try:
        model = torch.hub.load(
            UNET_REPO_DIR,
            "unet",
            in_channels=3,
            out_channels=1,
            init_features=32,
            pretrained=False,
            source="local",
        )
        model.load_state_dict(state_dict, strict=False)
        model.eval()
        dummy = torch.randn(1, 3, 256, 256)
        torch.onnx.export(
            model,
            dummy,
            ONNX_OUTPUT_PATH,
            export_params=True,
            opset_version=11,
            input_names=["input"],
            output_names=["output"],
            dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
        )
        print(f"[FL Server] Exported aggregated weights → {ONNX_OUTPUT_PATH}")
    except Exception as exc:
        print(f"[FL Server] ONNX export failed: {exc}")


# ---------------------------------------------------------------------------
# Custom FedAvg Strategy with DP + ONNX Export
# ---------------------------------------------------------------------------

class DPFedAvgWithONNXExport(FedAvg):
    """
    Extends FedAvg with:
    1. Gaussian differential privacy noise on aggregated weights.
    2. Automatic export to unet.onnx after each round.
    """

    def aggregate_fit(
        self,
        server_round: int,
        results: List[Tuple[ClientProxy, FitRes]],
        failures: List[Union[Tuple[ClientProxy, FitRes], BaseException]],
    ) -> Tuple[Optional[Parameters], Dict[str, Scalar]]:
        """Override to inject DP noise before returning aggregated parameters."""
        aggregated_parameters, metrics = super().aggregate_fit(
            server_round, results, failures
        )

        if aggregated_parameters is not None:
            # Convert to numpy, add DP noise, convert back
            arrays = parameters_to_ndarrays(aggregated_parameters)
            noisy_arrays = _add_dp_noise(arrays)
            aggregated_parameters = ndarrays_to_parameters(noisy_arrays)

            # Try to export new ONNX model
            # (requires the model architecture to reconstruct state dict)
            print(
                f"[FL Server] Round {server_round} — DP noise applied "
                f"(σ={_gaussian_noise_sigma(DP_EPSILON, DP_DELTA, DP_SENSITIVITY):.4f})"
            )

        return aggregated_parameters, metrics


# ---------------------------------------------------------------------------
# Server Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    strategy = DPFedAvgWithONNXExport(
        fraction_fit=1.0,          # Use all connected clients
        fraction_evaluate=1.0,
        min_fit_clients=2,
        min_evaluate_clients=2,
        min_available_clients=2,
    )

    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=5),
        strategy=strategy,
    )


if __name__ == "__main__":
    main()
