#!/usr/bin/env python3
"""
Download and Convert Real Training Datasets
===========================================
Downloads publicly available syscall anomaly detection datasets and converts
them to the format expected by the agent.

Supported Datasets:
1. ADFA-LD (Australian Defence Force Academy Linux Dataset)
2. DongTing Dataset (if available)
3. Other public datasets

Author: Likitha Shankar
"""

import sys
import os
import json
import argparse
import requests
import zipfile
import tarfile
from pathlib import Path
from typing import List, Tuple, Dict, Any
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def download_file(url: str, output_path: Path, chunk_size: int = 8192) -> bool:
    """Download a file from URL"""
    try:
        print(f"📥 Downloading from {url}...")
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r   Progress: {percent:.1f}%", end='', flush=True)
        
        print(f"\n✅ Downloaded to {output_path}")
        return True
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

def extract_archive(archive_path: Path, extract_to: Path) -> bool:
    """Extract zip or tar archive"""
    try:
        print(f"📦 Extracting {archive_path.name}...")
        extract_to.mkdir(parents=True, exist_ok=True)
        
        if archive_path.suffix == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        elif archive_path.suffix in ['.tar', '.gz', '.bz2'] or '.tar.' in archive_path.name:
            with tarfile.open(archive_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_to)
        else:
            print(f"⚠️  Unknown archive format: {archive_path.suffix}")
            return False
        
        print(f"✅ Extracted to {extract_to}")
        return True
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False

def convert_adfa_ld_format(adfa_dir: Path) -> List[Tuple[List[str], Dict]]:
    """
    Convert ADFA-LD dataset format to our training data format
    
    ADFA-LD structure:
    - Training_Data_Master/ (normal sequences)
    - Validation_Data_Master/ (normal sequences)
    - Attack_Data_Master/ (attack sequences)
    """
    training_data = []
    
    # Process normal sequences
    normal_dirs = ['Training_Data_Master', 'Validation_Data_Master']
    for dir_name in normal_dirs:
        normal_dir = adfa_dir / dir_name
        if not normal_dir.exists():
            continue
        
        print(f"📂 Processing {dir_name}...")
        for file_path in normal_dir.glob('*.txt'):
            try:
                with open(file_path, 'r') as f:
                    # ADFA-LD format: one syscall per line
                    syscalls = [line.strip() for line in f if line.strip()]
                
                if syscalls:
                    process_info = {
                        'cpu_percent': 10.0,  # Default values
                        'memory_percent': 5.0,
                        'num_threads': 1,
                        'pid': 0,
                        'source': 'ADFA-LD',
                        'label': 'normal'
                    }
                    training_data.append((syscalls, process_info))
            except Exception as e:
                print(f"⚠️  Error processing {file_path}: {e}")
    
    # Process attack sequences (for evaluation, not training)
    attack_dir = adfa_dir / 'Attack_Data_Master'
    if attack_dir.exists():
        print(f"📂 Processing Attack_Data_Master (for evaluation)...")
        attack_count = 0
        for file_path in attack_dir.glob('*.txt'):
            try:
                with open(file_path, 'r') as f:
                    syscalls = [line.strip() for line in f if line.strip()]
                
                if syscalls:
                    process_info = {
                        'cpu_percent': 15.0,
                        'memory_percent': 8.0,
                        'num_threads': 1,
                        'pid': 0,
                        'source': 'ADFA-LD',
                        'label': 'attack'
                    }
                    training_data.append((syscalls, process_info))
                    attack_count += 1
            except Exception as e:
                print(f"⚠️  Error processing {file_path}: {e}")
        
        print(f"   Found {attack_count} attack sequences (for evaluation)")
    
    return training_data

def download_adfa_ld(output_dir: Path) -> bool:
    """Download and convert ADFA-LD dataset"""
    print("\n" + "="*70)
    print("ADFA-LD Dataset Download")
    print("="*70)
    
    # ADFA-LD download URLs (these may need to be updated)
    # Note: Actual URLs may require registration or may have changed
    base_urls = [
        "https://www.unsw.adfa.edu.au/unsw-canberra-cyber/cybersecurity/ADFA-IDS-Datasets/",
        # Alternative sources may be available
    ]
    
    print("ℹ️  ADFA-LD Dataset Information:")
    print("   - Official site: https://www.unsw.adfa.edu.au/unsw-canberra-cyber/cybersecurity/ADFA-IDS-Datasets/")
    print("   - Format: Text files with one syscall per line")
    print("   - Contains: Normal sequences + Attack sequences")
    print("\n⚠️  Note: You may need to:")
    print("   1. Visit the official site to download")
    print("   2. Extract the archive manually")
    print("   3. Run this script with --adfa-dir pointing to extracted folder")
    
    return False  # Manual download required

def convert_dongting_format(dongting_dir: Path) -> List[Tuple[List[str], Dict]]:
    """
    Convert DongTing dataset format to our training data format
    
    DongTing dataset structure may vary - this is a template
    """
    training_data = []
    
    # This is a placeholder - actual format needs to be determined
    # when the dataset is downloaded
    print("⚠️  DongTing format converter - needs dataset structure analysis")
    
    return training_data

def download_dongting(output_dir: Path) -> bool:
    """Download and convert DongTing dataset"""
    print("\n" + "="*70)
    print("DongTing Dataset Download")
    print("="*70)
    
    # DongTing dataset from Zenodo
    zenodo_url = "https://zenodo.org/records/6627050"
    
    print(f"ℹ️  DongTing Dataset Information:")
    print(f"   - Zenodo: {zenodo_url}")
    print(f"   - Contains: 18,966 labeled normal and attack sequences")
    print(f"   - Covers: Linux kernels from past 5 years")
    print("\n⚠️  Note: You may need to:")
    print("   1. Visit Zenodo to download")
    print("   2. Extract the archive manually")
    print("   3. Run this script with --dongting-dir pointing to extracted folder")
    
    return False  # Manual download required

def save_training_data(training_data: List[Tuple[List[str], Dict]], 
                      output_file: Path, dataset_name: str) -> bool:
    """Save training data in our JSON format"""
    try:
        export_data = {
            'version': '1.0',
            'metadata': {
                'source': dataset_name,
                'total_samples': len(training_data),
                'feature_dimensions': 50,
                'format': 'syscall_sequences'
            },
            'samples': []
        }
        
        for syscalls, process_info in training_data:
            sample = {
                'syscalls': syscalls,
                'process_info': {
                    'cpu_percent': float(process_info.get('cpu_percent', 0.0)),
                    'memory_percent': float(process_info.get('memory_percent', 0.0)),
                    'num_threads': int(process_info.get('num_threads', 1)),
                    'pid': int(process_info.get('pid', 0)) if 'pid' in process_info else None
                }
            }
            if 'source' in process_info:
                sample['metadata'] = {'source': process_info['source'], 'label': process_info.get('label', 'normal')}
            export_data['samples'].append(sample)
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Saved {len(training_data)} samples to {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving training data: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Download and convert real training datasets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert ADFA-LD dataset (already downloaded)
  python3 scripts/download_real_datasets.py --adfa-dir /path/to/ADFA-LD --output datasets/adfa_ld_training.json
  
  # Convert DongTing dataset (already downloaded)
  python3 scripts/download_real_datasets.py --dongting-dir /path/to/DongTing --output datasets/dongting_training.json
  
  # Show download instructions
  python3 scripts/download_real_datasets.py --info
        """
    )
    
    parser.add_argument('--adfa-dir', type=str, help='Path to extracted ADFA-LD dataset directory')
    parser.add_argument('--dongting-dir', type=str, help='Path to extracted DongTing dataset directory')
    parser.add_argument('--output', type=str, default='datasets/real_training_data.json',
                       help='Output JSON file path (default: datasets/real_training_data.json)')
    parser.add_argument('--info', action='store_true', help='Show dataset information and download links')
    
    args = parser.parse_args()
    
    if args.info:
        print("\n" + "="*70)
        print("PUBLIC DATASETS FOR LINUX SYSCALL ANOMALY DETECTION")
        print("="*70)
        
        print("\n1. ADFA-LD (Australian Defence Force Academy Linux Dataset)")
        print("   URL: https://www.unsw.adfa.edu.au/unsw-canberra-cyber/cybersecurity/ADFA-IDS-Datasets/")
        print("   Format: Text files, one syscall per line")
        print("   Contains: Normal sequences + Attack sequences")
        print("   License: Academic use")
        
        print("\n2. DongTing Dataset")
        print("   URL: https://zenodo.org/records/6627050")
        print("   Size: 18,966 labeled sequences")
        print("   Coverage: Linux kernels from past 5 years")
        print("   License: Check Zenodo page")
        
        print("\n3. Other Potential Sources:")
        print("   - UNM datasets (University of New Mexico)")
        print("   - DARPA datasets (older, may have restrictions)")
        print("   - Academic research papers (check their supplementary materials)")
        
        print("\n" + "="*70)
        print("USAGE:")
        print("="*70)
        print("1. Download dataset from official source")
        print("2. Extract archive to a directory")
        print("3. Run: python3 scripts/download_real_datasets.py --adfa-dir /path/to/extracted --output datasets/adfa_training.json")
        print("4. Train models: python3 scripts/train_with_dataset.py --file datasets/adfa_training.json")
        return 0
    
    # Create output directory
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    training_data = []
    
    # Process ADFA-LD
    if args.adfa_dir:
        adfa_dir = Path(args.adfa_dir)
        if not adfa_dir.exists():
            print(f"❌ ADFA-LD directory not found: {adfa_dir}")
            return 1
        
        print("\n📂 Converting ADFA-LD dataset...")
        adfa_data = convert_adfa_ld_format(adfa_dir)
        training_data.extend(adfa_data)
        print(f"✅ Converted {len(adfa_data)} samples from ADFA-LD")
    
    # Process DongTing
    if args.dongting_dir:
        dongting_dir = Path(args.dongting_dir)
        if not dongting_dir.exists():
            print(f"❌ DongTing directory not found: {dongting_dir}")
            return 1
        
        print("\n📂 Converting DongTing dataset...")
        dongting_data = convert_dongting_format(dongting_dir)
        training_data.extend(dongting_data)
        print(f"✅ Converted {len(dongting_data)} samples from DongTing")
    
    if not training_data:
        print("\n❌ No training data converted. Use --info to see download instructions.")
        print("   Or provide --adfa-dir or --dongting-dir with extracted dataset directories.")
        return 1
    
    # Save converted data
    dataset_name = "real_dataset"
    if args.adfa_dir:
        dataset_name = "ADFA-LD"
    elif args.dongting_dir:
        dataset_name = "DongTing"
    
    if save_training_data(training_data, output_file, dataset_name):
        print(f"\n✅ Successfully converted and saved {len(training_data)} samples")
        print(f"📁 Output file: {output_file}")
        print(f"\n📝 Next steps:")
        print(f"   1. Review the data: cat {output_file} | head -50")
        print(f"   2. Train models: python3 scripts/train_with_dataset.py --file {output_file}")
        print(f"   3. Or combine with existing: python3 scripts/train_with_dataset.py --file {output_file} --append")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())

