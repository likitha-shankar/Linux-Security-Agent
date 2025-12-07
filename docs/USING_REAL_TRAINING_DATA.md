# Using Real Training Data from Public Datasets

This guide explains how to download and use real-world training data from publicly available datasets to improve your ML models.

## Available Public Datasets

### 1. ADFA-LD (Australian Defence Force Academy Linux Dataset)

**Best for**: Academic research, baseline comparison

- **URL**: https://www.unsw.adfa.edu.au/unsw-canberra-cyber/cybersecurity/ADFA-IDS-Datasets/
- **Format**: Text files, one syscall per line
- **Contains**: 
  - Normal sequences (Training_Data_Master, Validation_Data_Master)
  - Attack sequences (Attack_Data_Master)
- **License**: Academic use
- **Size**: ~1,000+ sequences

**Download Steps**:
1. Visit the official website
2. Download the dataset archive
3. Extract to a directory (e.g., `~/datasets/ADFA-LD/`)
4. Run conversion script:
   ```bash
   python3 scripts/download_real_datasets.py --adfa-dir ~/datasets/ADFA-LD --output datasets/adfa_ld_training.json
   ```

### 2. DongTing Dataset

**Best for**: Large-scale training, recent Linux kernels

- **URL**: https://zenodo.org/records/6627050
- **Format**: Varies (check Zenodo page)
- **Contains**: 18,966 labeled normal and attack sequences
- **Coverage**: Linux kernels from past 5 years
- **License**: Check Zenodo page

**Download Steps**:
1. Visit Zenodo page
2. Download the dataset
3. Extract to a directory
4. Run conversion script:
   ```bash
   python3 scripts/download_real_datasets.py --dongting-dir ~/datasets/DongTing --output datasets/dongting_training.json
   ```

## Quick Start

### Step 1: Get Dataset Information

```bash
python3 scripts/download_real_datasets.py --info
```

This shows:
- Available datasets
- Download URLs
- Usage instructions

### Step 2: Download Dataset

Manually download from the official source (most require registration or have specific terms).

### Step 3: Convert to Our Format

```bash
# For ADFA-LD
python3 scripts/download_real_datasets.py \
  --adfa-dir /path/to/extracted/ADFA-LD \
  --output datasets/adfa_ld_training.json

# For DongTing
python3 scripts/download_real_datasets.py \
  --dongting-dir /path/to/extracted/DongTing \
  --output datasets/dongting_training.json
```

### Step 4: Train Models

```bash
# Train with real data
python3 scripts/train_with_dataset.py --file datasets/adfa_ld_training.json

# Or combine with existing synthetic data
python3 scripts/train_with_dataset.py \
  --file datasets/adfa_ld_training.json \
  --file datasets/diverse_training_dataset.json \
  --append
```

## Benefits of Real Data

✅ **Better Generalization**: Models trained on real data perform better on real systems  
✅ **Academic Credibility**: Using established datasets strengthens your research  
✅ **Reproducibility**: Others can use the same datasets to verify your results  
✅ **Comparison**: Can compare against published results using same datasets  

## Format Requirements

The conversion script expects datasets in this format:

**ADFA-LD Format**:
```
Training_Data_Master/
  ├── file1.txt  (one syscall per line)
  ├── file2.txt
  └── ...

Validation_Data_Master/
  ├── file1.txt
  └── ...

Attack_Data_Master/
  ├── attack1.txt
  └── ...
```

**Our JSON Format** (output):
```json
{
  "version": "1.0",
  "metadata": {
    "source": "ADFA-LD",
    "total_samples": 1000,
    "feature_dimensions": 50
  },
  "samples": [
    {
      "syscalls": ["read", "write", "open", "close"],
      "process_info": {
        "cpu_percent": 10.0,
        "memory_percent": 5.0,
        "num_threads": 1
      },
      "metadata": {
        "source": "ADFA-LD",
        "label": "normal"
      }
    }
  ]
}
```

## Combining Datasets

You can combine multiple datasets for richer training:

```bash
# Train on multiple sources
python3 scripts/train_with_dataset.py \
  --file datasets/adfa_ld_training.json \
  --file datasets/diverse_training_dataset.json \
  --append
```

Or use the merge function programmatically:
```python
from core.enhanced_anomaly_detector import EnhancedAnomalyDetector

detector = EnhancedAnomalyDetector()
data1 = detector.load_training_data_from_file('datasets/adfa_ld_training.json')
data2 = detector.load_training_data_from_file('datasets/diverse_training_dataset.json')
combined = detector.merge_training_datasets(data1, data2)
detector.train_models(combined)
```

## Troubleshooting

### Dataset Format Issues

If the conversion script doesn't work, you may need to:
1. Check the actual dataset structure
2. Modify `convert_adfa_ld_format()` or `convert_dongting_format()` in the script
3. Create a custom converter for your dataset

### Missing Dependencies

```bash
pip install requests  # For URL downloads
```

### Large Datasets

For very large datasets:
- Process in batches
- Use `--append` flag for incremental training
- Consider sampling if dataset is too large

## Academic Citation

If you use these datasets, please cite them appropriately:

**ADFA-LD**:
```
Creech, G., & Hu, J. (2013). A semantic approach to host-based intrusion detection 
systems using contiguousand discontiguous system call patterns. 
IEEE Transactions on Computers, 62(6), 1012-1024.
```

**DongTing**:
```
[Check Zenodo page for citation information]
```

## Next Steps

1. ✅ Download a real dataset
2. ✅ Convert to our format
3. ✅ Train models with real data
4. ✅ Compare performance: real data vs synthetic data
5. ✅ Document results in your research

## Questions?

- Check dataset official pages for format details
- Review `scripts/download_real_datasets.py` for conversion logic
- Test with small subset first before full training

