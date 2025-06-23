"""
Main converter class for Transkribus to HuggingFace datasets.
"""

from typing import Optional, Dict, Any
from pathlib import Path
from datasets import Dataset
from huggingface_hub import HfApi, create_repo, get_token
import os

from .parser import TranskribusParser
from .exporters import (
    RawXMLExporter,
    TextExporter,
    RegionExporter,
    LineExporter,
    WindowExporter,
    BaseExporter
)


class TranskribusConverter:
    """Main converter class for converting Transkribus ZIP files to HuggingFace datasets."""
    
    EXPORT_MODES = {
        'raw_xml': RawXMLExporter,
        'text': TextExporter,
        'region': RegionExporter,
        'line': LineExporter,
        'window': WindowExporter,
    }
    
    def __init__(self, zip_path: str):
        """
        Initialize the converter.
        
        Args:
            zip_path: Path to the Transkribus ZIP file
        """
        self.zip_path = zip_path
        self.parser = TranskribusParser()
        self.pages = None
    
    def parse(self) -> None:
        """Parse the ZIP file and extract all page data."""
        print(f"Parsing ZIP file: {self.zip_path}")
        self.pages = self.parser.parse_zip(self.zip_path)
        print(f"Parsed {len(self.pages)} pages")
    
    def convert(self, export_mode: str = 'text', window_size: int = 2, overlap: int = 0) -> Dataset:
        """
        Convert parsed data to a HuggingFace dataset.
        
        Args:
            export_mode: Export mode ('raw_xml', 'text', 'region', 'line', 'window')
            window_size: Number of lines per window (only for window mode)
            overlap: Number of lines to overlap between windows (only for window mode)
            
        Returns:
            HuggingFace Dataset
        """
        if self.pages is None:
            self.parse()
        
        if export_mode not in self.EXPORT_MODES:
            raise ValueError(f"Invalid export mode: {export_mode}. Available modes: {list(self.EXPORT_MODES.keys())}")
        
        exporter_class = self.EXPORT_MODES[export_mode]
        
        # Handle window mode with special parameters
        if export_mode == 'window':
            exporter = exporter_class(self.zip_path, window_size=window_size, overlap=overlap)
            print(f"Converting to {export_mode} format (window_size={window_size}, overlap={overlap})...")
        else:
            exporter = exporter_class(self.zip_path)
            print(f"Converting to {export_mode} format...")
        
        dataset = exporter.export(self.pages)
        print(f"Created dataset with {len(dataset)} examples")
        
        return dataset
    
    def upload_to_hub(
        self,
        dataset: Dataset,
        repo_id: str,
        token: Optional[str] = None,
        private: bool = False,
        commit_message: Optional[str] = None
    ) -> str:
        """
        Upload dataset to HuggingFace Hub.
        
        Args:
            dataset: The dataset to upload
            repo_id: Repository ID (e.g., "username/dataset-name")
            token: HuggingFace token (if None, will try to get from cache or HF_TOKEN env var)
            private: Whether to make the repo private
            commit_message: Custom commit message
            
        Returns:
            Repository URL
        """
        # Try to get token in this order:
        # 1. Explicit token parameter
        # 2. HF_TOKEN environment variable
        # 3. HuggingFace cache (from huggingface-cli login)
        if token is None:
            token = os.getenv('HF_TOKEN')
            if token is None:
                try:
                    token = get_token()
                except Exception:
                    pass
        
        # If still no token, provide helpful error message
        if token is None:
            raise ValueError(
                "No HuggingFace token found. Please either:\n"
                "1. Run 'huggingface-cli login' to authenticate\n"
                "2. Set HF_TOKEN environment variable\n"
                "3. Pass token parameter directly"
            )
        
        # Create repository if it doesn't exist
        try:
            create_repo(
                repo_id=repo_id,
                repo_type="dataset",
                private=private,
                token=token,
                exist_ok=True
            )
            print(f"Repository {repo_id} created/verified")
        except Exception as e:
            print(f"Error creating repository: {e}")
            raise
        
        # Upload dataset
        if commit_message is None:
            commit_message = f"Upload Transkribus dataset from {Path(self.zip_path).name}"
        
        print(f"Uploading dataset to {repo_id}...")
        dataset.push_to_hub(
            repo_id=repo_id,
            token=token,
            commit_message=commit_message
        )
        
        repo_url = f"https://huggingface.co/datasets/{repo_id}"
        print(f"Dataset uploaded successfully: {repo_url}")
        return repo_url
    
    def convert_and_upload(
        self,
        repo_id: str,
        export_mode: str = 'text',
        token: Optional[str] = None,
        private: bool = False,
        commit_message: Optional[str] = None,
        window_size: int = 2,
        overlap: int = 0
    ) -> str:
        """
        Convert and upload in one step.
        
        Args:
            repo_id: Repository ID (e.g., "username/dataset-name")
            export_mode: Export mode ('raw_xml', 'text', 'region', 'line', 'window')
            token: HuggingFace token
            private: Whether to make the repo private
            commit_message: Custom commit message
            window_size: Number of lines per window (only for window mode)
            overlap: Number of lines to overlap between windows (only for window mode)
            
        Returns:
            Repository URL
        """
        dataset = self.convert(export_mode=export_mode, window_size=window_size, overlap=overlap)
        return self.upload_to_hub(
            dataset=dataset,
            repo_id=repo_id,
            token=token,
            private=private,
            commit_message=commit_message
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the parsed data.
        
        Returns:
            Dictionary with statistics
        """
        if self.pages is None:
            self.parse()
        
        total_regions = sum(len(page.regions) for page in self.pages)
        total_lines = sum(
            len(region.text_lines) 
            for page in self.pages 
            for region in page.regions
        )
        
        projects = set(page.project_name for page in self.pages)
        
        return {
            'total_pages': len(self.pages),
            'total_regions': total_regions,
            'total_lines': total_lines,
            'projects': list(projects),
            'avg_regions_per_page': total_regions / len(self.pages) if self.pages else 0,
            'avg_lines_per_page': total_lines / len(self.pages) if self.pages else 0,
        } 