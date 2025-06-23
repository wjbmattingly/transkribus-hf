"""
Command-line interface for transkribus-hf.
"""

import argparse
import sys
from pathlib import Path

from .converter import TranskribusConverter


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert Transkribus ZIP files to HuggingFace datasets"
    )
    
    parser.add_argument(
        "zip_path",
        help="Path to the Transkribus ZIP file"
    )
    
    parser.add_argument(
        "--mode",
        choices=['raw_xml', 'text', 'region', 'line', 'window'],
        default='text',
        help="Export mode (default: text)"
    )
    
    parser.add_argument(
        "--window-size",
        type=int,
        default=2,
        help="Number of lines per window (only for window mode, default: 2)"
    )
    
    parser.add_argument(
        "--overlap",
        type=int,
        default=0,
        help="Number of lines to overlap between windows (only for window mode, default: 0)"
    )
    
    parser.add_argument(
        "--repo-id",
        help="HuggingFace repository ID (e.g., username/dataset-name)"
    )
    
    parser.add_argument(
        "--token",
        help="HuggingFace token (or set HF_TOKEN environment variable)"
    )
    
    parser.add_argument(
        "--private",
        action="store_true",
        help="Make the repository private"
    )
    
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show statistics, don't convert or upload"
    )
    
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Convert but don't upload to HuggingFace Hub"
    )
    
    parser.add_argument(
        "--output-dir",
        help="Directory to save the dataset locally (when using --local-only)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not Path(args.zip_path).exists():
        print(f"Error: ZIP file not found: {args.zip_path}")
        sys.exit(1)
    
    if not args.stats_only and not args.local_only and not args.repo_id:
        print("Error: --repo-id is required unless using --stats-only or --local-only")
        sys.exit(1)
    
    # Validate window parameters
    if args.mode == 'window':
        if args.window_size < 1:
            print("Error: --window-size must be at least 1")
            sys.exit(1)
        if args.overlap < 0:
            print("Error: --overlap cannot be negative")
            sys.exit(1)
        if args.overlap >= args.window_size:
            print("Error: --overlap must be less than --window-size")
            sys.exit(1)
    
    # Initialize converter
    converter = TranskribusConverter(args.zip_path)
    
    # Show statistics if requested
    if args.stats_only:
        stats = converter.get_stats()
        print("Dataset Statistics:")
        print(f"  Total pages: {stats['total_pages']}")
        print(f"  Total regions: {stats['total_regions']}")
        print(f"  Total lines: {stats['total_lines']}")
        print(f"  Projects: {', '.join(stats['projects'])}")
        print(f"  Avg regions per page: {stats['avg_regions_per_page']:.1f}")
        print(f"  Avg lines per page: {stats['avg_lines_per_page']:.1f}")
        
        # For window mode, show expected window count
        if args.mode == 'window':
            step = args.window_size - args.overlap
            estimated_windows = 0
            for stat in ['total_regions']:  # This is a rough estimate
                regions_with_lines = stats['total_lines'] // 5  # rough estimate
                estimated_windows += max(0, regions_with_lines - args.window_size + 1) // step
            print(f"  Estimated windows (window_size={args.window_size}, overlap={args.overlap}): ~{estimated_windows}")
        
        return
    
    try:
        # Convert the dataset
        dataset = converter.convert(
            export_mode=args.mode,
            window_size=args.window_size,
            overlap=args.overlap
        )
        
        if args.local_only:
            # Save locally
            mode_suffix = f"_{args.mode}"
            if args.mode == 'window':
                mode_suffix += f"_w{args.window_size}_o{args.overlap}"
            output_dir = args.output_dir or f"./transkribus_dataset{mode_suffix}"
            dataset.save_to_disk(output_dir)
            print(f"Dataset saved to: {output_dir}")
        else:
            # Upload to HuggingFace Hub
            repo_url = converter.upload_to_hub(
                dataset=dataset,
                repo_id=args.repo_id,
                token=args.token,
                private=args.private
            )
            print(f"Success! Dataset available at: {repo_url}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 