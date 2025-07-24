#!/usr/bin/env python3
"""
Example usage of the transkribus-hf package.
"""

import os
from pathlib import Path
from transkribus_hf import TranskribusConverter


def main():
    """Example usage of transkribus-hf."""
    
    # Path to your Transkribus ZIP file
    zip_path = "/home/wjbmattingly/data/export_job_16945702.zip"
    
    # Check if file exists
    if not Path(zip_path).exists():
        print(f"Please update the zip_path variable to point to your Transkribus ZIP file")
        print(f"Current path: {zip_path}")
        return
    
    # Initialize the converter
    print("Initializing Transkribus converter...")
    converter = TranskribusConverter(zip_path)
    
    # Get statistics about the data
    print("\n" + "="*50)
    print("DATASET STATISTICS")
    print("="*50)
    stats = converter.get_stats()
    print(f"Total pages: {stats['total_pages']}")
    print(f"Total regions: {stats['total_regions']}")
    print(f"Total lines: {stats['total_lines']}")
    print(f"Projects: {', '.join(stats['projects'])}")
    print(f"Average regions per page: {stats['avg_regions_per_page']:.1f}")
    print(f"Average lines per page: {stats['avg_lines_per_page']:.1f}")
    
    # Example 1: Convert to text format (default)
    print("\n" + "="*50)
    print("EXAMPLE 1: TEXT FORMAT")
    print("="*50)
    text_dataset = converter.convert(export_mode='text')
    print(f"Created text dataset with {len(text_dataset)} examples")
    print("Sample entry:")
    if len(text_dataset) > 0:
        sample = text_dataset[0]
        print(f"  Filename: {sample['filename']}")
        print(f"  Project: {sample['project']}")
        print(f"  Text preview: {sample['text'][:200]}...")
    
    # Example 2: Convert to region format
    print("\n" + "="*50)
    print("EXAMPLE 2: REGION FORMAT")
    print("="*50)
    region_dataset = converter.convert(export_mode='region')
    print(f"Created region dataset with {len(region_dataset)} examples")
    print("Sample region:")
    if len(region_dataset) > 0:
        sample = region_dataset[0]
        print(f"  Region ID: {sample['region_id']}")
        print(f"  Region type: {sample['region_type']}")
        print(f"  Reading order: {sample['reading_order']}")
        print(f"  Text: {sample['text'][:100]}...")
    
    # Example 3: Convert to line format
    print("\n" + "="*50)
    print("EXAMPLE 3: LINE FORMAT")
    print("="*50)
    line_dataset = converter.convert(export_mode='line')
    print(f"Created line dataset with {len(line_dataset)} examples")
    print("Sample line:")
    if len(line_dataset) > 0:
        sample = line_dataset[0]
        print(f"  Line ID: {sample['line_id']}")
        print(f"  Region ID: {sample['region_id']}")
        print(f"  Line reading order: {sample['line_reading_order']}")
        print(f"  Region reading order: {sample['region_reading_order']}")
        print(f"  Text: {sample['text']}")
    
    # Example 4: Convert to raw XML format
    print("\n" + "="*50)
    print("EXAMPLE 4: RAW XML FORMAT")
    print("="*50)
    xml_dataset = converter.convert(export_mode='raw_xml')
    print(f"Created XML dataset with {len(xml_dataset)} examples")
    print("Sample XML entry:")
    if len(xml_dataset) > 0:
        sample = xml_dataset[0]
        print(f"  Filename: {sample['filename']}")
        print(f"  XML preview: {sample['xml'][:300]}...")
    
    # Example 5: Convert to polygon region format (NEW!)
    print("\n" + "="*50)
    print("EXAMPLE 5: POLYGON REGION FORMAT")
    print("="*50)
    polygon_region_dataset = converter.convert(export_mode='polygon_region')
    print(f"Created polygon region dataset with {len(polygon_region_dataset)} examples")
    print("Sample polygon region:")
    if len(polygon_region_dataset) > 0:
        sample = polygon_region_dataset[0]
        print(f"  Region ID: {sample['region_id']}")
        print(f"  Region type: {sample['region_type']}")
        print(f"  Reading order: {sample['reading_order']}")
        print(f"  Coordinates: {sample['coords'][:100]}...")
        print(f"  Text: {sample['text'][:100]}...")
    
    # Example 6: Convert to polygon line format (NEW!)
    print("\n" + "="*50)
    print("EXAMPLE 6: POLYGON LINE FORMAT")
    print("="*50)
    polygon_line_dataset = converter.convert(export_mode='polygon_line')
    print(f"Created polygon line dataset with {len(polygon_line_dataset)} examples")
    print("Sample polygon line:")
    if len(polygon_line_dataset) > 0:
        sample = polygon_line_dataset[0]
        print(f"  Line ID: {sample['line_id']}")
        print(f"  Region ID: {sample['region_id']}")
        print(f"  Reading order: {sample['reading_order']}")
        print(f"  Coordinates: {sample['coords'][:100]}...")
        print(f"  Baseline: {sample.get('baseline', 'None')}")
        print(f"  Text: {sample['text']}")
    
    # Example 7: Convert to window format
    print("\n" + "="*50)
    print("EXAMPLE 7: WINDOW FORMAT")
    print("="*50)
    window_dataset = converter.convert(export_mode='window', window_size=3, overlap=1)
    print(f"Created window dataset with {len(window_dataset)} examples (window_size=3, overlap=1)")
    print("Sample window:")
    if len(window_dataset) > 0:
        sample = window_dataset[0]
        print(f"  Window size: {sample['window_size']}")
        print(f"  Window index: {sample['window_index']}")
        print(f"  Line IDs: {sample['line_ids']}")
        print(f"  Text: {sample['text'][:150]}...")
    
    # Example 8: Save datasets locally
    print("\n" + "="*50)
    print("EXAMPLE 8: SAVING LOCALLY")
    print("="*50)
    output_dir = "./example_datasets"
    
    # Save different formats
    text_dataset.save_to_disk(f"{output_dir}/text_format")
    region_dataset.save_to_disk(f"{output_dir}/region_format")
    line_dataset.save_to_disk(f"{output_dir}/line_format")
    xml_dataset.save_to_disk(f"{output_dir}/xml_format")
    polygon_region_dataset.save_to_disk(f"{output_dir}/polygon_region_format")
    polygon_line_dataset.save_to_disk(f"{output_dir}/polygon_line_format")
    window_dataset.save_to_disk(f"{output_dir}/window_format")
    
    print(f"Datasets saved to {output_dir}/")
    print("- text_format/")
    print("- region_format/")
    print("- line_format/")
    print("- xml_format/")
    print("- polygon_region_format/")
    print("- polygon_line_format/")
    print("- window_format/")
    
    # Example 9: Upload to HuggingFace Hub (commented out)
    print("\n" + "="*50)
    print("EXAMPLE 9: UPLOAD TO HUGGINGFACE HUB")
    print("="*50)
    print("To upload to HuggingFace Hub, uncomment the following code:")
    print("Make sure to set your HF_TOKEN environment variable or pass the token parameter")
    print()
    print("# Upload text dataset")
    repo_url = converter.upload_to_hub(
        dataset=text_dataset,
        repo_id='wjbmattingly/my-transkribus-dataset',
        private=True
    )
    print("# )")
    print("# print(f'Dataset uploaded: {repo_url}')")
    print()
    print("# Or convert and upload in one step:")
    print("# repo_url = converter.convert_and_upload(")
    print("#     repo_id='wjbmattingly/my-transkribus-dataset-lines',")
    print("#     export_mode='line',")
    print("#     private=False")
    print("# )")
    
    print("\n" + "="*50)
    print("EXAMPLES COMPLETED")
    print("="*50)


if __name__ == "__main__":
    main()