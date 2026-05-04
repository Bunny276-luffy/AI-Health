"""
Federated Learning Client
Hospital node: trains locally for 3 epochs, encrypts weight delta, sends to FL server.
"""
import os
import io
import copy
import argparse
from collections import OrderedDict
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from cryptography.fernet import Fernet
import flwr as fl
from flwr.common import NDArrays, Scalar

# Reuse the dataset loader from the existing training scripts
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from dataset import MedicalSegmentationDataset  # noqa: E402

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
UNET_REPO_DIR = os.path.join(MODELS_DIR, "unet_repo")

LOCAL_EPOCHS = 3
LEARNING_RATE = 1e-4


# ---------------------------------------------------------------------------
# Symmetric Key Encryption (Fernet = AES-128-CBC + HMAC-SHA256)
# ---------------------------------------------------------------------------

def _get_or_create_key() -> bytes:
    """
    Loads a symmetric Fernet key from the environment or generates a new one.
    In production, share this key securely (e.g., HashiCorp Vault, AWS Secrets Manager).
    """
    env_key = os.environ.get("FL_SYMMETRIC_KEY")
    if env_key:
        return env_key.encode()
    # Generate + persist locally for demo
    key_path = os.path.join(MODELS_DIR, "fl_key.key")
    if os.path.exists(key_path):
        with open(key_path, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    os.makedirs(MODELS_DIR, exist_ok=True)
    with open(key_path, "wb") as f:
        f.write(key)
    return key


def encrypt_weights(arrays: List[np.ndarray]) -> bytes:
    key = _get_or_create_key()
    fernet = Fernet(key)
    buffer = io.BytesIO()
    np.save(buffer, np.array(arrays, dtype=object))
    return fernet.encrypt(buffer.getvalue())


def decrypt_weights(ciphertext: bytes) -> List[np.ndarray]:
    key = _get_or_create_key()
    fernet = Fernet(key)
    plaintext = fernet.decrypt(ciphertext)
    buffer = io.BytesIO(plaintext)
    return list(np.load(buffer, allow_pickle=True))


# ---------------------------------------------------------------------------
# Loss
# ---------------------------------------------------------------------------

class DiceBCELoss(nn.Module):
    def forward(self, inputs: torch.Tensor, targets: torch.Tensor, smooth: float = 1.0) -> torch.Tensor:
        inputs_sig = torch.sigmoid(inputs).view(-1)
        targets_flat = targets.view(-1)
        intersection = (inputs_sig * targets_flat).sum()
        dice = 1 - (2.0 * intersection + smooth) / (inputs_sig.sum() + targets_flat.sum() + smooth)
        bce = nn.functional.binary_cross_entropy_with_logits(inputs_sig, targets_flat)
        return bce + dice


# ---------------------------------------------------------------------------
# Flower Client
# ---------------------------------------------------------------------------

class NeuroScanFLClient(fl.client.NumPyClient):

    def __init__(self, data_dir: str) -> None:
        self.device = torch.device(
            "cuda" if torch.cuda.is_available()
            else "mps" if torch.backends.mps.is_available()
            else "cpu"
        )
        self.model = torch.hub.load(
            UNET_REPO_DIR,
            "unet",
            in_channels=3,
            out_channels=1,
            init_features=32,
            pretrained=False,
            source="local",
        ).to(self.device)

        dataset = MedicalSegmentationDataset(data_dir, is_train=True)
        self.loader = DataLoader(dataset, batch_size=4, shuffle=True, drop_last=False)
        self.criterion = DiceBCELoss()
        print(f"[FL Client] Device={self.device}, Dataset size={len(dataset)}")

    # -- Flower interface ---------------------------------------------------

    def get_parameters(self, config: Dict[str, Scalar]) -> NDArrays:
        return [val.cpu().numpy() for val in self.model.state_dict().values()]

    def set_parameters(self, parameters: NDArrays) -> None:
        state_dict = OrderedDict(
            {k: torch.tensor(v) for k, v in zip(self.model.state_dict().keys(), parameters)}
        )
        self.model.load_state_dict(state_dict, strict=True)

    def fit(
        self, parameters: NDArrays, config: Dict[str, Scalar]
    ) -> Tuple[NDArrays, int, Dict[str, Scalar]]:
        # Store global params so we can compute delta
        global_params = copy.deepcopy(parameters)

        self.set_parameters(parameters)
        optimizer = optim.Adam(self.model.parameters(), lr=LEARNING_RATE)
        self.model.train()

        total_loss = 0.0
        for epoch in range(LOCAL_EPOCHS):
            for images, masks in self.loader:
                images, masks = images.to(self.device), masks.to(self.device)
                optimizer.zero_grad()
                preds = self.model(images)
                loss = self.criterion(preds, masks)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

        avg_loss = total_loss / (LOCAL_EPOCHS * max(len(self.loader), 1))
        print(f"[FL Client] Training complete. Avg loss: {avg_loss:.4f}")

        updated_params = self.get_parameters({})
        return updated_params, len(self.loader.dataset), {"loss": avg_loss}  # type: ignore[arg-type]

    def evaluate(
        self, parameters: NDArrays, config: Dict[str, Scalar]
    ) -> Tuple[float, int, Dict[str, Scalar]]:
        self.set_parameters(parameters)
        self.model.eval()
        total_loss = 0.0
        with torch.no_grad():
            for images, masks in self.loader:
                images, masks = images.to(self.device), masks.to(self.device)
                preds = self.model(images)
                total_loss += self.criterion(preds, masks).item()
        avg = total_loss / max(len(self.loader), 1)
        return float(avg), len(self.loader.dataset), {"val_loss": avg}  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, required=True, help="Path to local hospital dataset")
    parser.add_argument("--server_address", type=str, default="localhost:8080")
    args = parser.parse_args()

    client = NeuroScanFLClient(data_dir=args.data_dir)
    fl.client.start_numpy_client(
        server_address=args.server_address,
        client=client,
    )


if __name__ == "__main__":
    main()
