# Transkribus-HF

Convert Transkribus ZIP files to HuggingFace datasets with ease.

## Overview

`transkribus-hf` is a Python package that converts Transkribus export ZIP files into HuggingFace datasets. It supports multiple export formats and can automatically upload datasets to the HuggingFace Hub.

## Features

- **Multiple Export Modes**: Convert your Transkribus data to different dataset formats
- **Automatic Upload**: Direct integration with HuggingFace Hub
- **Region & Line Extraction**: Extract individual text regions and lines as separate images
- **Windowed Extraction**: Create sliding windows of multiple lines for data augmentation
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

### 5. Window (`window`) - NEW!
Exports sliding windows of multiple text lines, perfect for data augmentation and multi-line text recognition training.

**Configuration:**
- `window_size`: Number of lines per window (1, 2, 3, 4, etc.)
- `overlap`: Number of lines to overlap between windows (0 = no overlap)

**Fields:**
- `image`: Cropped window image (bounding box of all lines in window)
- `text`: Combined text from all lines in window (newline separated)
- `window_size`: Actual number of lines in this window
- `window_index`: Index of this window within the region
- `line_ids`: Comma-separated list of line IDs in this window
- `line_reading_orders`: Comma-separated list of line reading orders
- `region_id`: Parent region identifier
- `region_reading_order`: Reading order of parent region
- `region_type`: Type of parent region
- `filename`: Original image filename
- `project`: Project name

**Examples:**
- `window_size=1, overlap=0`: Same as line mode
- `window_size=2, overlap=0`: Non-overlapping pairs of lines
- `window_size=3, overlap=1`: 3-line windows with 1-line overlap (lines 1-3, 2-4, 3-5, etc.)
- `window_size=4, overlap=2`: 4-line windows with 2-line overlap (lines 1-4, 3-6, 5-8, etc.)

## Usage

### Command Line Interface

```bash
# Basic usage - convert and upload to HuggingFace Hub
transkribus-hf path/to/your/transkribus.zip --repo-id username/dataset-name

# Specify export mode
transkribus-hf path/to/your/transkribus.zip --repo-id username/dataset-name --mode region

# Window mode with 3 lines per window, 1 line overlap
transkribus-hf path/to/your/transkribus.zip --repo-id username/dataset-name --mode window --window-size 3 --overlap 1

# Convert to local directory only
transkribus-hf path/to/your/transkribus.zip --local-only --output-dir ./my_dataset

# View statistics only (including window estimates)
transkribus-hf path/to/your/transkribus.zip --stats-only --mode window --window-size 2

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

# NEW: Window mode with different configurations
window_2_dataset = converter.convert(export_mode='window', window_size=2, overlap=0)
window_3_overlap_dataset = converter.convert(export_mode='window', window_size=3, overlap=1)
window_4_dataset = converter.convert(export_mode='window', window_size=4, overlap=2)

print(f"2-line windows: {len(window_2_dataset)} examples")
print(f"3-line windows (1 overlap): {len(window_3_overlap_dataset)} examples")
print(f"4-line windows (2 overlap): {len(window_4_dataset)} examples")

# Upload to HuggingFace Hub
repo_url = converter.upload_to_hub(
    dataset=window_3_overlap_dataset,
    repo_id="wjbmattingly/my-transkribus-windows",
    private=False
)
print(f"Dataset uploaded: {repo_url}")

# Convert and upload in one step
repo_url = converter.convert_and_upload(
    repo_id="wjbmattingly/my-transkribus-dataset",
    export_mode="window",
    window_size=2,
    overlap=1,
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

## Window Mode Use Cases

The window mode is particularly useful for:

1. **Data Augmentation**: Generate more training examples from existing data
2. **Multi-line Text Recognition**: Train models to recognize multiple lines at once
3. **Reading Order Training**: Train models to understand line sequences
4. **Flexible Context**: Adjust context size (1-4+ lines) based on your needs
5. **Overlapping Context**: Create overlapping examples for better generalization

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
