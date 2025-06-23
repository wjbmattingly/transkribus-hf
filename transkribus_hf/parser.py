"""
Parser for Transkribus ZIP files and PAGE XML format.
"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import re
import chardet

@dataclass
class TextLine:
    """Represents a text line in the PAGE XML."""
    id: str
    text: str
    coords: List[Tuple[int, int]]
    baseline: Optional[List[Tuple[int, int]]]
    reading_order: int
    region_id: str

@dataclass
class TextRegion:
    """Represents a text region in the PAGE XML."""
    id: str
    type: str
    coords: List[Tuple[int, int]]
    text_lines: List[TextLine]
    reading_order: int
    full_text: str

@dataclass
class PageData:
    """Represents a complete page with metadata and content."""
    image_filename: str
    image_width: int
    image_height: int
    regions: List[TextRegion]
    xml_content: str
    project_name: str

class TranskribusParser:
    """Parser for Transkribus ZIP files containing PAGE XML format."""
    
    def __init__(self):
        self.namespace = {
            'pc': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'
        }
    
    def parse_zip(self, zip_path: str) -> List[PageData]:
        """
        Parse a Transkribus ZIP file and extract all page data.
        
        Args:
            zip_path: Path to the ZIP file
            
        Returns:
            List of PageData objects
        """
        pages = []
        
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            # Get all files in the ZIP
            file_list = zip_file.namelist()
            
            # Group files by project (top-level directory)
            projects = self._group_files_by_project(file_list)
            
            for project_name, project_files in projects.items():
                # Find XML files in the page subdirectory, filtering out macOS metadata
                xml_files = [
                    f for f in project_files 
                    if f.endswith('.xml') and '/page/' in f 
                    and not self._is_macos_metadata_file(f)
                ]
                
                for xml_file in xml_files:
                    try:
                        # Read XML content with encoding detection
                        xml_content = self._read_xml_with_encoding(zip_file, xml_file)
                        
                        if xml_content is None:
                            continue
                        
                        # Parse the XML
                        page_data = self._parse_page_xml(xml_content, project_name)
                        if page_data:
                            pages.append(page_data)
                    except Exception as e:
                        print(f"Error parsing {xml_file}: {e}")
                        continue
        
        return pages
    
    def _group_files_by_project(self, file_list: List[str]) -> Dict[str, List[str]]:
        """Group files by their top-level directory (project)."""
        projects = {}
        
        for file_path in file_list:
            if '/' in file_path:
                project_name = file_path.split('/')[0]
                if project_name not in projects:
                    projects[project_name] = []
                projects[project_name].append(file_path)
        
        return projects
    
    def _is_macos_metadata_file(self, file_path: str) -> bool:
        """Check if a file is a macOS metadata file that should be skipped."""
        # Skip __MACOSX directory and ._ prefixed files
        if '__MACOSX' in file_path or file_path.startswith('._'):
            return True
        
        # Skip other common macOS metadata patterns
        if '/.' in file_path and not file_path.endswith('.xml'):
            return True
        
        return False
    
    def _read_xml_with_encoding(self, zip_file: zipfile.ZipFile, xml_file: str) -> Optional[str]:
        """Read XML content with automatic encoding detection and fallback."""
        try:
            # First try UTF-8
            raw_content = zip_file.read(xml_file)
            try:
                return raw_content.decode('utf-8')
            except UnicodeDecodeError:
                pass
            
            # Try to detect encoding using chardet
            try:
                detected = chardet.detect(raw_content)
                if detected and detected['confidence'] > 0.7:
                    encoding = detected['encoding']
                    if encoding:
                        try:
                            return raw_content.decode(encoding)
                        except (UnicodeDecodeError, LookupError):
                            pass
            except ImportError:
                # chardet not available, try common encodings
                pass
            
            # Fallback to common encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    return raw_content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            
            print(f"Could not decode {xml_file} with any supported encoding")
            return None
            
        except Exception as e:
            print(f"Error reading {xml_file}: {e}")
            return None
    
    def _parse_page_xml(self, xml_content: str, project_name: str) -> Optional[PageData]:
        """Parse a single PAGE XML file."""
        try:
            root = ET.fromstring(xml_content)
            
            # Get page element
            page_elem = root.find('pc:Page', self.namespace)
            if page_elem is None:
                return None
            
            # Extract page metadata
            image_filename = page_elem.get('imageFilename', '')
            image_width = int(page_elem.get('imageWidth', 0))
            image_height = int(page_elem.get('imageHeight', 0))
            
            # Parse reading order
            reading_order = self._parse_reading_order(root)
            
            # Parse text regions
            regions = self._parse_text_regions(root, reading_order)
            
            return PageData(
                image_filename=image_filename,
                image_width=image_width,
                image_height=image_height,
                regions=regions,
                xml_content=xml_content,
                project_name=project_name
            )
            
        except ET.ParseError as e:
            print(f"XML parsing error: {e}")
            return None
    
    def _parse_reading_order(self, root: ET.Element) -> Dict[str, int]:
        """Parse the reading order from the XML."""
        reading_order = {}
        
        reading_order_elem = root.find('.//pc:ReadingOrder', self.namespace)
        if reading_order_elem is not None:
            for region_ref in reading_order_elem.findall('.//pc:RegionRefIndexed', self.namespace):
                region_id = region_ref.get('regionRef', '')
                index = int(region_ref.get('index', 0))
                reading_order[region_id] = index
        
        return reading_order
    
    def _parse_text_regions(self, root: ET.Element, reading_order: Dict[str, int]) -> List[TextRegion]:
        """Parse all text regions from the XML."""
        regions = []
        
        for region_elem in root.findall('.//pc:TextRegion', self.namespace):
            region_id = region_elem.get('id', '')
            region_type = region_elem.get('type', 'paragraph')
            
            # Parse coordinates
            coords = self._parse_coords(region_elem.find('pc:Coords', self.namespace))
            
            # Parse text lines
            text_lines = self._parse_text_lines(region_elem, region_id)
            
            # Get full text from TextEquiv
            full_text = self._get_text_equiv(region_elem)
            
            # Get reading order
            region_reading_order = reading_order.get(region_id, 0)
            
            region = TextRegion(
                id=region_id,
                type=region_type,
                coords=coords,
                text_lines=text_lines,
                reading_order=region_reading_order,
                full_text=full_text
            )
            
            regions.append(region)
        
        # Sort regions by reading order
        regions.sort(key=lambda r: r.reading_order)
        
        return regions
    
    def _parse_text_lines(self, region_elem: ET.Element, region_id: str) -> List[TextLine]:
        """Parse text lines within a region."""
        lines = []
        
        for line_elem in region_elem.findall('pc:TextLine', self.namespace):
            line_id = line_elem.get('id', '')
            
            # Parse coordinates
            coords = self._parse_coords(line_elem.find('pc:Coords', self.namespace))
            
            # Parse baseline
            baseline_elem = line_elem.find('pc:Baseline', self.namespace)
            baseline = self._parse_coords(baseline_elem) if baseline_elem is not None else None
            
            # Get text content
            text = self._get_text_equiv(line_elem)
            
            # Extract reading order from custom attribute
            reading_order = self._extract_reading_order_from_custom(line_elem)
            
            line = TextLine(
                id=line_id,
                text=text,
                coords=coords,
                baseline=baseline,
                reading_order=reading_order,
                region_id=region_id
            )
            
            lines.append(line)
        
        # Sort lines by reading order
        lines.sort(key=lambda l: l.reading_order)
        
        return lines
    
    def _parse_coords(self, coords_elem: Optional[ET.Element]) -> List[Tuple[int, int]]:
        """Parse coordinates from a Coords element."""
        if coords_elem is None:
            return []
        
        points_str = coords_elem.get('points', '')
        if not points_str:
            return []
        
        coords = []
        for point in points_str.split():
            if ',' in point:
                x, y = point.split(',')
                coords.append((int(x), int(y)))
        
        return coords
    
    def _get_text_equiv(self, element: ET.Element) -> str:
        """Extract text from TextEquiv/Unicode element."""
        text_equiv = element.find('pc:TextEquiv/pc:Unicode', self.namespace)
        if text_equiv is not None and text_equiv.text:
            return text_equiv.text
        return ""
    
    def _extract_reading_order_from_custom(self, element: ET.Element) -> int:
        """Extract reading order from custom attribute."""
        custom = element.get('custom', '')
        if 'readingOrder' in custom:
            match = re.search(r'readingOrder\s*\{\s*index\s*:\s*(\d+)', custom)
            if match:
                return int(match.group(1))
        return 0 