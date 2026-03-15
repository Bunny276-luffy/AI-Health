import os
import requests
import zipfile
import torch

def download_file_with_resume(url, filepath):
    headers = {}
    if os.path.exists(filepath):
        downloaded = os.path.getsize(filepath)
        headers['Range'] = f'bytes={downloaded}-'
    else:
        downloaded = 0
        
    print(f"Downloading {url} to {filepath} (Resuming from {downloaded} bytes)")
    
    response = requests.get(url, headers=headers, stream=True, timeout=15)
    
    # If the server honors Range requests, it returns 206 Partial Content
    # If it returns 200, it's starting from the beginning
    mode = 'ab' if response.status_code == 206 else 'wb'
    
    if response.status_code in [200, 206]:
        with open(filepath, mode) as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print("Download complete.")
    else:
        print(f"Failed to download. Status code: {response.status_code}")

def main():
    hub_dir = os.path.expanduser("~/.cache/torch/hub")
    os.makedirs(hub_dir, exist_ok=True)
    
    repo_zip = os.path.join(hub_dir, "mateuszbuda_brain-segmentation-pytorch_master.zip")
    url = "https://github.com/mateuszbuda/brain-segmentation-pytorch/archive/master.zip"
    
    # Retry loop
    max_retries = 10
    for i in range(max_retries):
        try:
            download_file_with_resume(url, repo_zip)
            break
        except Exception as e:
            print(f"Attempt {i+1} failed: {e}")
            import time; time.sleep(2)
            
    print("Now loading model to trigger weight download...")
    # This might still fail when downloading the weights (.pt file). Let's see.
    import export_unet
    export_unet.main()
    
if __name__ == "__main__":
    main()
