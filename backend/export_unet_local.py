import torch
import os

def main():
    print("Loading U-Net from local cloned repo...")
    # Get absolute path to models/unet_repo
    repo_dir = os.path.abspath(os.path.join("models", "unet_repo"))
    
    if not os.path.exists(repo_dir):
        print(f"Error: {repo_dir} does not exist.")
        return

    try:
        model = torch.hub.load(
            repo_dir, 
            'unet',
            in_channels=3, 
            out_channels=1, 
            init_features=32, 
            pretrained=False, 
            source='local'
        )
    except Exception as e:
        print(f"Failed to load via PyTorch Hub: {e}")
        # If weights download fails, initialize without pretrained
        print("Fallback: Initializing without pretrained weights to proceed mapping ONNX architecture...")
        model = torch.hub.load(
            repo_dir, 
            'unet',
            in_channels=3, 
            out_channels=1, 
            init_features=32, 
            pretrained=False, 
            source='local'
        )

    model.eval()

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

    print(f"PyTorch model successfully exported to ONNX format ({onnx_path})!")

if __name__ == "__main__":
    main()
