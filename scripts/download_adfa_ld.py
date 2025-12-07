#!/usr/bin/env python3
"""
Download ADFA-LD Dataset
========================
Attempts to download ADFA-LD dataset from various sources
"""

import sys
import os
import requests
import zipfile
import tarfile
from pathlib import Path

def download_from_github():
    """Try to download from GitHub repositories"""
    print("="*70)
    print("ATTEMPTING TO DOWNLOAD ADFA-LD DATASET")
    print("="*70)
    
    # Known GitHub repositories with ADFA-LD data
    github_repos = [
        "https://github.com/verazuo/a-labelled-version-of-the-ADFA-LD-dataset/archive/refs/heads/main.zip",
        "https://github.com/fkie-cad/COMIDDS/archive/refs/heads/main.zip",
    ]
    
    download_dir = Path.home() / "datasets" / "ADFA-LD"
    download_dir.mkdir(parents=True, exist_ok=True)
    
    for repo_url in github_repos:
        try:
            print(f"\n📥 Trying: {repo_url}")
            archive_path = download_dir / "dataset.zip"
            
            response = requests.get(repo_url, stream=True, timeout=120)
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                print(f"   Downloading ({total_size / 1024 / 1024:.1f} MB)...")
                with open(archive_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                print(f"\r   Progress: {percent:.1f}%", end='', flush=True)
                
                print(f"\n✅ Downloaded successfully!")
                print(f"📦 Extracting...")
                
                # Extract
                extract_to = download_dir / "extracted"
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
                
                print(f"✅ Extracted to: {extract_to}")
                print(f"\n📝 Next step:")
                print(f"   python3 scripts/download_real_datasets.py --adfa-dir {extract_to} --output datasets/adfa_training.json")
                return True
            else:
                print(f"   ❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    return False

def download_sample_data():
    """Download a smaller sample if full dataset not available"""
    print("\n" + "="*70)
    print("DOWNLOADING SAMPLE DATA")
    print("="*70)
    
    # Try to get sample data from various sources
    sample_urls = [
        "https://raw.githubusercontent.com/fkie-cad/COMIDDS/main/datasets/adfa_ld_sample.json",
    ]
    
    for url in sample_urls:
        try:
            print(f"\n📥 Trying sample data: {url}")
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                output_file = Path("datasets") / "adfa_sample.json"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ Downloaded sample to: {output_file}")
                return True
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    return False

if __name__ == "__main__":
    print("\n🔍 Searching for ADFA-LD dataset download sources...")
    
    # Try full dataset first
    if download_from_github():
        print("\n✅ Successfully downloaded ADFA-LD dataset!")
        sys.exit(0)
    
    # Try sample data
    if download_sample_data():
        print("\n✅ Downloaded sample data (use for testing)")
        sys.exit(0)
    
    print("\n" + "="*70)
    print("⚠️  AUTOMATIC DOWNLOAD NOT AVAILABLE")
    print("="*70)
    print("\nMost datasets require manual download due to:")
    print("  - Terms of service")
    print("  - Registration requirements")
    print("  - Large file sizes")
    print("\n📝 Manual Download Instructions:")
    print("\n1. ADFA-LD Dataset:")
    print("   - Visit: https://www.unsw.adfa.edu.au/unsw-canberra-cyber/cybersecurity/ADFA-IDS-Datasets/")
    print("   - Or: https://github.com/verazuo/a-labelled-version-of-the-ADFA-LD-dataset")
    print("   - Download and extract to ~/datasets/ADFA-LD/")
    print("   - Then run: python3 scripts/download_real_datasets.py --adfa-dir ~/datasets/ADFA-LD --output datasets/adfa_training.json")
    print("\n2. DongTing Dataset:")
    print("   - Visit: https://zenodo.org/records/6627050")
    print("   - Download and extract")
    print("   - Then run: python3 scripts/download_real_datasets.py --dongting-dir /path/to/extracted --output datasets/dongting_training.json")
    print("\n" + "="*70)
    
    sys.exit(1)

