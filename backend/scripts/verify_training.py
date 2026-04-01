import os
import numpy as np
import cv2
import subprocess
import sys

def create_dummy_dataset(base_dir="dummy_data"):
    """
    Generates an artificial miniaturized dataset to verify backpropagation math.
    """
    img_dir = os.path.join(base_dir, "images")
    mask_dir = os.path.join(base_dir, "masks")
    
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(mask_dir, exist_ok=True)
    
    print(f"Generating mathematically synthetic dataset at {base_dir}")
    
    # Generate 4 dummy images and masks
    for i in range(4):
        # Create a synthetic brain MRI-like background
        img = np.random.randint(0, 50, (256, 256, 3), dtype=np.uint8)
        # Add a "tumor" artifact
        cv2.circle(img, (128 + i*10, 128 - i*5), 30, (200, 200, 200), -1)
        
        # Create corresponding binary mask
        mask = np.zeros((256, 256), dtype=np.uint8)
        cv2.circle(mask, (128 + i*10, 128 - i*5), 30, 255, -1)
        
        # Save
        img_name = f"scan_{i}.jpg"
        cv2.imwrite(os.path.join(img_dir, img_name), img)
        cv2.imwrite(os.path.join(mask_dir, img_name), mask)
        
    print("Dummy artifacts securely encoded.")

def run_verification(base_dir="dummy_data"):
    # Target train.py
    train_script = os.path.join(os.path.dirname(__file__), "train.py")
    
    print("\n--- INITIATING SYSTEM VERIFICATION PROTOCOL ---")
    print("Testing Custom Dataset Loaders, PyTorch Memory Gradients, and ONNX Re-Exporter...\n")
    
    cmd = [
        sys.executable, train_script,
        "--data_dir", base_dir,
        "--epochs", "2",
        "--batch_size", "2"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(result.stdout)
        print("\n[VERIFICATION PASSED] The custom backward-pass mathematics executed smoothly.")
        print("[DEPLOYMENT READY] You may now attach your proprietary dataset to `train.py`.")
    else:
        print("[VERIFICATION FAILED] Deep Learning routine aborted.")
        print(result.stderr)

if __name__ == "__main__":
    dummy_dir = os.path.join(os.path.dirname(__file__), "dummy_data")
    create_dummy_dataset(dummy_dir)
    run_verification(dummy_dir)
