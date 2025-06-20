# Transkribus-HF

Convert Transkribus ZIP files to HuggingFace datasets with ease.

## Overview

`transkribus-hf` is a Python package that converts Transkribus export ZIP files into HuggingFace datasets. It supports multiple export formats and can automatically upload datasets to the HuggingFace Hub.

## Features

- **Multiple Export Modes**: Convert your Transkribus data to different dataset formats
- **Automatic Upload**: Direct integration with HuggingFace Hub
- **Region & Line Extraction**: Extract individual text regions and lines as separate images
- **Preserves Metadata**: Maintains reading order, region types, and other important metadata
- **Command Line Interface**: Easy-to-use CLI for batch processing

## Installation

```bash
pip install transkribus-hf
```

Or install from source:

```bash
git clone https://github.com/wjbmattingly/transkribus-hf.git
cd transkribus-hf
pip install -e .
```

## Export Modes

### 1. Raw XML (`raw_xml`)
Exports the original image with the complete PAGE XML content.

**Fields:**
- `image`: Original page image
- `xml`: Complete PAGE XML content
- `filename`: Original image filename
- `project`: Project name

### 2. Text (`text`) - Default
Exports the image with concatenated text from all regions.

**Fields:**
- `image`: Original page image
- `text`: Full text content (all regions combined)
- `filename`: Original image filename
- `project`: Project name

### 3. Region (`region`)
Exports each text region as a separate cropped image.

**Fields:**
- `image`: Cropped region image
- `text`: Region text content
- `region_type`: Type of region (e.g., "paragraph")
- `region_id`: Unique region identifier
- `reading_order`: Reading order of the region
- `filename`: Original image filename
- `project`: Project name

### 4. Line (`line`)
Exports each text line as a separate cropped image.

**Fields:**
- `image`: Cropped line image
- `text`: Line text content
- `line_id`: Unique line identifier
- `line_reading_order`: Reading order within the region
- `region_id`: Parent region identifier
- `region_reading_order`: Reading order of parent region
- `region_type`: Type of parent region
- `filename`: Original image filename
- `project`: Project name

## Usage

### Command Line Interface

```bash
# Basic usage - convert and upload to HuggingFace Hub
transkribus-hf path/to/your/transkribus.zip --repo-id username/dataset-name

# Specify export mode
transkribus-hf path/to/your/transkribus.zip --repo-id username/dataset-name --mode region

# Convert to local directory only
transkribus-hf path/to/your/transkribus.zip --local-only --output-dir ./my_dataset

# View statistics only
transkribus-hf path/to/your/transkribus.zip --stats-only

# Create private repository
transkribus-hf path/to/your/transkribus.zip --repo-id username/dataset-name --private

# Use custom HuggingFace token
transkribus-hf path/to/your/transkribus.zip --repo-id username/dataset-name --token your_token_here
```

### Python API

```python
from transkribus_hf import TranskribusConverter

# Initialize converter
converter = TranskribusConverter("path/to/your/transkribus.zip")

# Get statistics
stats = converter.get_stats()
print(f"Total pages: {stats['total_pages']}")
print(f"Total regions: {stats['total_regions']}")
print(f"Total lines: {stats['total_lines']}")

# Convert to dataset (text mode)
dataset = converter.convert(export_mode='text')
print(f"Created dataset with {len(dataset)} examples")

# Convert to different modes
region_dataset = converter.convert(export_mode='region')
line_dataset = converter.convert(export_mode='line')
xml_dataset = converter.convert(export_mode='raw_xml')

# Upload to HuggingFace Hub
repo_url = converter.upload_to_hub(
    dataset=dataset,
    repo_id="wjbmattingly/my-transkribus-dataset",
    private=False
)
print(f"Dataset uploaded: {repo_url}")

# Convert and upload in one step
repo_url = converter.convert_and_upload(
    repo_id="wjbmattingly/my-transkribus-dataset",
    export_mode="line",
    private=False
)
```

## Transkribus ZIP Structure

The package expects Transkribus ZIP files with the following structure:

```
transkribus_export.zip
├── project1/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── page/
│       ├── image1.xml
│       └── image2.xml
├── project2/
│   ├── image3.jpg
│   └── page/
│       └── image3.xml
└── ...
```

## Authentication

To upload datasets to HuggingFace Hub, you need to authenticate:

1. Set environment variable: `export HF_TOKEN=your_token_here`
2. Or pass the token directly: `--token your_token_here`
3. Or use `huggingface-cli login`

## Requirements

- Python ≥ 3.8
- datasets ≥ 2.0.0
- huggingface_hub ≥ 0.15.0
- Pillow ≥ 9.0.0
- lxml ≥ 4.6.0
- numpy ≥ 1.21.0
- tqdm ≥ 4.62.0

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Citation

If you use this package in your research, please cite:

```bibtex
@software{mattingly2024_transkribus_hf,
  author = {Mattingly, William J.B.},
  title = {transkribus-hf: Convert Transkribus ZIP files to HuggingFace datasets},
  year = {2024},
  publisher = {GitHub},
  url = {https://github.com/wjbmattingly/transkribus-hf}
}
``` 