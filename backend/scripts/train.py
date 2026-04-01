import os
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from dataset import MedicalSegmentationDataset

class DiceBCELoss(nn.Module):
    """
    Combined BCE and Dice Loss for robust medical segmentation.
    BCE stabilizes the gradient, while Dice handles severe class imbalance.
    """
    def __init__(self, weight=None, size_average=True):
        super(DiceBCELoss, self).__init__()

    def forward(self, inputs, targets, smooth=1):
        # Flatten probabilities and targets
        inputs = torch.sigmoid(inputs).view(-1)
        targets = targets.view(-1)
        
        intersection = (inputs * targets).sum()                            
        dice_loss = 1 - (2.*intersection + smooth)/(inputs.sum() + targets.sum() + smooth)  
        bce = nn.functional.binary_cross_entropy_with_logits(inputs, targets, reduction='mean')
        
        return bce + dice_loss

def get_unet_model():
    """
    Loads the identical U-Net architecture from the existing local repo
    used to export the initial ONNX weights.
    """
    repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "unet_repo"))
    
    # We load with pretrained=False because we are going to train it ourselves
    model = torch.hub.load(
        repo_dir, 
        'unet',
        in_channels=3, 
        out_channels=1, 
        init_features=32, 
        pretrained=False, 
        source='local'
    )
    return model

def export_to_onnx(model, save_path):
    print(f"\n[+] Compressing trained weights into Edge Execution Engine Format: {save_path}")
    model.eval()
    
    # Create dummy input that matches inference specification
    dummy_input = torch.randn(1, 3, 256, 256, device=next(model.parameters()).device)
    
    torch.onnx.export(
        model, 
        dummy_input, 
        save_path, 
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
    )
    print(f"[SUCCESS] Native ONNX export complete! FastAPI backend is ready to serve predictions.")

def main():
    parser = argparse.ArgumentParser(description="Medical Image Segmentation Training Loop")
    parser.add_argument("--data_dir", type=str, required=True, help="Directory containing /images and /masks")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate for Adam")
    args = parser.parse_args()
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
    print(f"[System] Selected Hardware Accelerator: {device}")
    
    # 1. Prepare Data
    print(f"[Loading] Linking image tensors and ground-truth annotation maps from {args.data_dir}...")
    train_dataset = MedicalSegmentationDataset(args.data_dir, is_train=True)
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, drop_last=True)
    print(f"[Ready] Found {len(train_dataset)} scans. Epochs: {args.epochs}, Batch Size: {args.batch_size}")
    
    # 2. Setup Model, Loss, Optimizer
    model = get_unet_model().to(device)
    criterion = DiceBCELoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    
    # 3. Main Training Loop
    print("\n[+] Initiating PyTorch Backpropagation Routine...")
    for epoch in range(1, args.epochs + 1):
        model.train()
        epoch_loss = 0.0
        
        for batch_idx, (images, masks) in enumerate(train_loader):
            images, masks = images.to(device), masks.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            
            loss = criterion(outputs, masks)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            
            if batch_idx % max(1, len(train_loader) // 5) == 0:
                print(f"Epoch [{epoch}/{args.epochs}] Batch [{batch_idx}/{len(train_loader)}] Loss: {loss.item():.4f}")
                
        avg_loss = epoch_loss / len(train_loader)
        print(f"====> Epoch {epoch} Completed | Average Loss: {avg_loss:.4f} <====")

    # 4. Persistence
    models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    os.makedirs(models_dir, exist_ok=True)
    
    model_save_path = os.path.join(models_dir, "custom_unet.pt")
    torch.save(model.state_dict(), model_save_path)
    print(f"\n[+] PyTorch Weights saved securely to: {model_save_path}")
    
    # 5. Overwrite the Edge Optimized ONNX Graph with new weights
    onnx_target = os.path.abspath(os.path.join(models_dir, "unet.onnx"))
    export_to_onnx(model, onnx_target)

if __name__ == "__main__":
    main()
