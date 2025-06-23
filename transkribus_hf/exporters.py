"""
Exporters for converting parsed Transkribus data to different HuggingFace dataset formats.
"""

import zipfile
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image, ImageFile
import io
import numpy as np
from datasets import Dataset, Features, Value, Image as DatasetImage

from .parser import PageData, TextRegion, TextLine

# Allow loading of truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True


class BaseExporter(ABC):
    """Base class for all exporters."""
    
    def __init__(self, zip_path: str):
        self.zip_path = zip_path
        self.failed_images = []
        self.processed_count = 0
        self.skipped_count = 0
    
    @abstractmethod
    def export(self, pages: List[PageData]) -> Dataset:
        """Export pages to a HuggingFace dataset."""
        pass
    
    def _load_image_from_zip(self, zip_file: zipfile.ZipFile, image_path: str) -> Optional[Image.Image]:
        """Load an image from the ZIP file with robust error handling."""
        try:
            image_data = zip_file.read(image_path)
            
            # Try to open the image
            image = Image.open(io.BytesIO(image_data))
            
            # Verify the image by trying to load it completely
            image.verify()
            
            # Reload the image for actual use (verify() invalidates the image)
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary (handles various formats)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
            
        except Exception as e:
            error_msg = f"Error loading image {image_path}: {e}"
            print(f"Warning: {error_msg}")
            self.failed_images.append((image_path, str(e)))
            self.skipped_count += 1
            return None
    
    def _find_image_path(self, zip_file: zipfile.ZipFile, page: PageData) -> Optional[str]:
        """Find the image path in the ZIP file for a given page."""
        # Look for the image in the project directory
        possible_paths = [
            f"{page.project_name}/{page.image_filename}",
            f"{page.project_name}/images/{page.image_filename}",
            page.image_filename
        ]
        
        file_list = zip_file.namelist()
        for path in possible_paths:
            if path in file_list:
                return path
        
        # If exact match not found, try to find by filename
        for file_path in file_list:
            if file_path.endswith(page.image_filename):
                return file_path
        
        return None
    
    def _crop_region(self, image: Image.Image, coords: List[Tuple[int, int]]) -> Optional[Image.Image]:
        """Crop a region from an image based on coordinates."""
        if not coords:
            return None
        
        try:
            # Calculate bounding box
            x_coords = [coord[0] for coord in coords]
            y_coords = [coord[1] for coord in coords]
            
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            
            # Ensure coordinates are within image bounds
            min_x = max(0, min_x)
            min_y = max(0, min_y)
            max_x = min(image.width, max_x)
            max_y = min(image.height, max_y)
            
            # Check if the crop area is valid
            if min_x >= max_x or min_y >= max_y:
                print(f"Warning: Invalid crop coordinates: ({min_x}, {min_y}, {max_x}, {max_y})")
                return None
            
            return image.crop((min_x, min_y, max_x, max_y))
        except Exception as e:
            print(f"Warning: Error cropping region: {e}")
            return None
    
    def _calculate_bounding_box(self, coords_list: List[List[Tuple[int, int]]]) -> List[Tuple[int, int]]:
        """Calculate the bounding box that encompasses multiple coordinate sets."""
        if not coords_list:
            return []
        
        all_coords = []
        for coords in coords_list:
            all_coords.extend(coords)
        
        if not all_coords:
            return []
        
        x_coords = [coord[0] for coord in all_coords]
        y_coords = [coord[1] for coord in all_coords]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        # Return as rectangle coordinates
        return [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]
    
    def _print_summary(self):
        """Print processing summary."""
        print(f"\nProcessing Summary:")
        print(f"  Successfully processed: {self.processed_count}")
        print(f"  Skipped due to errors: {self.skipped_count}")
        if self.failed_images:
            print(f"  Failed images:")
            for image_path, error in self.failed_images[:5]:  # Show first 5 errors
                print(f"    {image_path}: {error}")
            if len(self.failed_images) > 5:
                print(f"    ... and {len(self.failed_images) - 5} more")


class RawXMLExporter(BaseExporter):
    """Export raw images with their corresponding XML content."""
    
    def export(self, pages: List[PageData]) -> Dataset:
        """Export pages as image + raw XML pairs."""
        
        def generate_examples():
            with zipfile.ZipFile(self.zip_path, 'r') as zip_file:
                for page in pages:
                    image_path = self._find_image_path(zip_file, page)
                    if image_path:
                        image = self._load_image_from_zip(zip_file, image_path)
                        if image:
                            self.processed_count += 1
                            
                            yield {
                                'image': image,
                                'xml': page.xml_content,
                                'filename': page.image_filename,
                                'project': page.project_name
                            }
        
        features = Features({
            'image': DatasetImage(),
            'xml': Value('string'),
            'filename': Value('string'),
            'project': Value('string')
        })
        
        dataset = Dataset.from_generator(
            generate_examples,
            features=features,
            cache_dir=None
        )
        
        self._print_summary()
        return dataset


class TextExporter(BaseExporter):
    """Export images with concatenated text content."""
    
    def export(self, pages: List[PageData]) -> Dataset:
        """Export pages as image + full text pairs."""
        
        def generate_examples():
            with zipfile.ZipFile(self.zip_path, 'r') as zip_file:
                for page in pages:
                    image_path = self._find_image_path(zip_file, page)
                    if image_path:
                        image = self._load_image_from_zip(zip_file, image_path)
                        if image:
                            # Concatenate all text from regions in reading order
                            full_text = '\n'.join([region.full_text for region in page.regions if region.full_text])
                            
                            self.processed_count += 1
                            
                            yield {
                                'image': image,
                                'text': full_text,
                                'filename': page.image_filename,
                                'project': page.project_name
                            }
        
        features = Features({
            'image': DatasetImage(),
            'text': Value('string'),
            'filename': Value('string'),
            'project': Value('string')
        })
        
        dataset = Dataset.from_generator(
            generate_examples,
            features=features,
            cache_dir=None
        )
        
        self._print_summary()
        return dataset


class RegionExporter(BaseExporter):
    """Export individual regions as separate images with metadata."""
    
    def export(self, pages: List[PageData]) -> Dataset:
        """Export each region as a separate dataset entry."""
        
        def generate_examples():
            with zipfile.ZipFile(self.zip_path, 'r') as zip_file:
                for page in pages:
                    image_path = self._find_image_path(zip_file, page)
                    if image_path:
                        full_image = self._load_image_from_zip(zip_file, image_path)
                        if full_image:
                            for region in page.regions:
                                region_image = self._crop_region(full_image, region.coords)
                                if region_image:
                                    self.processed_count += 1
                                    
                                    yield {
                                        'image': region_image,
                                        'text': region.full_text,
                                        'region_type': region.type,
                                        'region_id': region.id,
                                        'reading_order': region.reading_order,
                                        'filename': page.image_filename,
                                        'project': page.project_name
                                    }
        
        features = Features({
            'image': DatasetImage(),
            'text': Value('string'),
            'region_type': Value('string'),
            'region_id': Value('string'),
            'reading_order': Value('int32'),
            'filename': Value('string'),
            'project': Value('string')
        })
        
        dataset = Dataset.from_generator(
            generate_examples,
            features=features,
            cache_dir=None
        )
        
        self._print_summary()
        return dataset


class LineExporter(BaseExporter):
    """Export individual text lines as separate images with metadata."""
    
    def export(self, pages: List[PageData]) -> Dataset:
        """Export each text line as a separate dataset entry."""
        
        def generate_examples():
            with zipfile.ZipFile(self.zip_path, 'r') as zip_file:
                for page in pages:
                    image_path = self._find_image_path(zip_file, page)
                    if image_path:
                        full_image = self._load_image_from_zip(zip_file, image_path)
                        if full_image:
                            for region in page.regions:
                                for line in region.text_lines:
                                    line_image = self._crop_region(full_image, line.coords)
                                    if line_image:
                                        self.processed_count += 1
                                        
                                        yield {
                                            'image': line_image,
                                            'text': line.text,
                                            'line_id': line.id,
                                            'line_reading_order': line.reading_order,
                                            'region_id': line.region_id,
                                            'region_reading_order': region.reading_order,
                                            'region_type': region.type,
                                            'filename': page.image_filename,
                                            'project': page.project_name
                                        }
        
        features = Features({
            'image': DatasetImage(),
            'text': Value('string'),
            'line_id': Value('string'),
            'line_reading_order': Value('int32'),
            'region_id': Value('string'),
            'region_reading_order': Value('int32'),
            'region_type': Value('string'),
            'filename': Value('string'),
            'project': Value('string')
        })
        
        dataset = Dataset.from_generator(
            generate_examples,
            features=features,
            cache_dir=None
        )
        
        self._print_summary()
        return dataset


class WindowExporter(BaseExporter):
    """Export sliding windows of text lines with configurable window size and overlap."""
    
    def __init__(self, zip_path: str, window_size: int = 2, overlap: int = 0):
        """
        Initialize the window exporter.
        
        Args:
            zip_path: Path to the ZIP file
            window_size: Number of lines per window (1, 2, 3, etc.)
            overlap: Number of lines to overlap between windows
        """
        super().__init__(zip_path)
        self.window_size = window_size
        self.overlap = overlap
        
        if overlap >= window_size:
            raise ValueError("Overlap must be less than window size")
    
    def export(self, pages: List[PageData]) -> Dataset:
        """Export sliding windows of lines as separate dataset entries."""
        
        def generate_examples():
            with zipfile.ZipFile(self.zip_path, 'r') as zip_file:
                for page in pages:
                    image_path = self._find_image_path(zip_file, page)
                    if image_path:
                        full_image = self._load_image_from_zip(zip_file, image_path)
                        if full_image:
                            for region in page.regions:
                                # Generate sliding windows for this region
                                windows = self._create_windows(region.text_lines)
                                
                                for window_idx, window_lines in enumerate(windows):
                                    # Calculate bounding box for all lines in this window
                                    line_coords = [line.coords for line in window_lines if line.coords]
                                    if line_coords:
                                        window_coords = self._calculate_bounding_box(line_coords)
                                        window_image = self._crop_region(full_image, window_coords)
                                        
                                        if window_image:
                                            # Combine text from all lines in window
                                            window_text = '\n'.join([line.text for line in window_lines if line.text])
                                            
                                            # Create line info for metadata
                                            line_ids = [line.id for line in window_lines]
                                            line_orders = [line.reading_order for line in window_lines]
                                            
                                            self.processed_count += 1
                                            
                                            yield {
                                                'image': window_image,
                                                'text': window_text,
                                                'window_size': len(window_lines),
                                                'window_index': window_idx,
                                                'line_ids': ', '.join(line_ids),
                                                'line_reading_orders': ', '.join(map(str, line_orders)),
                                                'region_id': region.id,
                                                'region_reading_order': region.reading_order,
                                                'region_type': region.type,
                                                'filename': page.image_filename,
                                                'project': page.project_name
                                            }
        
        # Create dataset using generator to avoid memory issues
        features = Features({
            'image': DatasetImage(),
            'text': Value('string'),
            'window_size': Value('int32'),
            'window_index': Value('int32'),
            'line_ids': Value('string'),
            'line_reading_orders': Value('string'),
            'region_id': Value('string'),
            'region_reading_order': Value('int32'),
            'region_type': Value('string'),
            'filename': Value('string'),
            'project': Value('string')
        })
        
        dataset = Dataset.from_generator(
            generate_examples,
            features=features,
            cache_dir=None  # Disable caching to save memory
        )
        
        self._print_summary()
        return dataset
    
    def _create_windows(self, lines: List[TextLine]) -> List[List[TextLine]]:
        """Create sliding windows of lines with specified size and overlap."""
        if not lines:
            return []
        
        windows = []
        step = self.window_size - self.overlap
        
        for i in range(0, len(lines), step):
            window = lines[i:i + self.window_size]
            if len(window) > 0:  # Always include windows, even if smaller than window_size
                windows.append(window)
            
            # Stop if we've reached the end and the last window would be too small
            # (unless we want to include partial windows)
            if i + self.window_size >= len(lines):
                break
        
        return windows 