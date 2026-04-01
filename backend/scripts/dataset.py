import os
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset
import torchvision.transforms.functional as TF
import random

class MedicalSegmentationDataset(Dataset):
    """
    Standard PyTorch Dataset for loading medical images and binary masks.
    Expects a folder structure:
        data_dir/
            ├── images/
            │   ├── img1.jpg
            │   ├── img2.jpg
            │   └── ...
            └── masks/
                ├── img1.jpg  (matching filename)
                ├── img2.jpg
                └── ...
    """
    def __init__(self, data_dir, image_size=(256, 256), is_train=True):
        self.data_dir = data_dir
        self.image_dir = os.path.join(data_dir, "images")
        self.mask_dir = os.path.join(data_dir, "masks")
        self.image_size = image_size
        self.is_train = is_train
        
        # Verify directories exist
        if not os.path.exists(self.image_dir) or not os.path.exists(self.mask_dir):
            raise FileNotFoundError(f"Missing images or masks directory in {data_dir}")
            
        # Get list of files
        self.image_filenames = sorted(os.listdir(self.image_dir))
        
        # Filter valid extensions
        valid_exts = {'.png', '.jpg', '.jpeg', '.dcm'}
        self.image_filenames = [f for f in self.image_filenames if os.path.splitext(f)[1].lower() in valid_exts]
        
    def __len__(self):
        return len(self.image_filenames)

    def __getitem__(self, idx):
        img_name = self.image_filenames[idx]
        img_path = os.path.join(self.image_dir, img_name)
        
        # We assume masks have the exact same filename. If user uses PNG masks for JPG images, 
        # a more robust filename matching function is required.
        mask_path = os.path.join(self.mask_dir, img_name)
        
        # Read image (RGB expected by MateuszBuda UNet)
        image = cv2.imread(img_path, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Failed to read image at {img_path}")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Read mask (Grayscale)
        if not os.path.exists(mask_path):
            raise FileNotFoundError(f"Missing corresponding mask for {img_name} at {mask_path}")
            
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        if mask is None:
            raise ValueError(f"Failed to read mask at {mask_path}")
            
        # Resize
        image = cv2.resize(image, self.image_size)
        mask = cv2.resize(mask, self.image_size, interpolation=cv2.INTER_NEAREST)
        
        # Convert to arrays
        image = np.array(image, dtype=np.float32) / 255.0
        mask = np.array(mask, dtype=np.float32) / 255.0  # Normalize to [0...1]
        
        # Ensure mask is exactly binary (0 or 1)
        mask = (mask > 0.5).astype(np.float32)
        
        # Convert to Tensors
        # Image shape: [C, H, W]
        image_tensor = torch.from_numpy(image.transpose(2, 0, 1))
        # Mask shape: [1, H, W]
        mask_tensor = torch.from_numpy(mask).unsqueeze(0)
        
        # Data Augmentation (Train only)
        if self.is_train:
            # Random Horizontal Flip
            if random.random() > 0.5:
                image_tensor = TF.hflip(image_tensor)
                mask_tensor = TF.hflip(mask_tensor)
                
            # Random Vertical Flip
            if random.random() > 0.5:
                image_tensor = TF.vflip(image_tensor)
                mask_tensor = TF.vflip(mask_tensor)
                
        # ImageNet Standardization required by the U-Net model
        image_tensor = TF.normalize(
            image_tensor,
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
        
        return image_tensor, mask_tensor
