import torch
import os

def main():
    print("Downloading U-Net from PyTorch Hub...")
    # Mateusz Buda Brain Segmentation PyTorch model
    model = torch.hub.load('mateuszbuda/brain-segmentation-pytorch', 'unet',
        in_channels=3, out_channels=1, init_features=32, pretrained=True)

    model.eval()

    # Dummy input matching the expected input shape (Batch Size, Channels, Height, Width)
    dummy_input = torch.randn(1, 3, 256, 256)

    onnx_dir = "models"
    os.makedirs(onnx_dir, exist_ok=True)
    onnx_path = os.path.join(onnx_dir, "unet.onnx")
    
    print(f"Exporting model to {onnx_path}...")
    torch.onnx.export(
        model, 
        dummy_input, 
        onnx_path, 
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
    )

    print("PyTorch model successfully exported to ONNX format!")

if __name__ == "__main__":
    main()
