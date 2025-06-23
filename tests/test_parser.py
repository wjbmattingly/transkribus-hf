"""
Basic tests for the transkribus-hf parser.
"""

import unittest
from unittest.mock import patch, mock_open
import xml.etree.ElementTree as ET

from transkribus_hf.parser import TranskribusParser, PageData, TextRegion, TextLine


class TestTranskribusParser(unittest.TestCase):
    """Test cases for TranskribusParser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = TranskribusParser()
        
        # Sample XML content based on the provided example
        self.sample_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15">
    <Page imageFilename="test.jpg" imageWidth="1247" imageHeight="1920">
        <ReadingOrder>
            <OrderedGroup id="ro_test">
                <RegionRefIndexed index="0" regionRef="region_1"/>
                <RegionRefIndexed index="1" regionRef="region_2"/>
            </OrderedGroup>
        </ReadingOrder>
        <TextRegion type="paragraph" id="region_1">
            <Coords points="5,3 100,3 100,50 5,50"/>
            <TextLine id="line_1" custom="readingOrder {index:0;}">
                <Coords points="10,10 90,10 90,30 10,30"/>
                <TextEquiv>
                    <Unicode>Test line 1</Unicode>
                </TextEquiv>
            </TextLine>
            <TextLine id="line_2" custom="readingOrder {index:1;}">
                <Coords points="10,35 90,35 90,45 10,45"/>
                <TextEquiv>
                    <Unicode>Test line 2</Unicode>
                </TextEquiv>
            </TextLine>
            <TextEquiv>
                <Unicode>Test line 1
Test line 2</Unicode>
            </TextEquiv>
        </TextRegion>
    </Page>
</PcGts>'''
    
    def test_parse_coords(self):
        """Test coordinate parsing."""
        root = ET.fromstring(self.sample_xml)
        coords_elem = root.find('.//pc:Coords', self.parser.namespace)
        
        coords = self.parser._parse_coords(coords_elem)
        expected = [(5, 3), (100, 3), (100, 50), (5, 50)]
        
        self.assertEqual(coords, expected)
    
    def test_parse_reading_order(self):
        """Test reading order parsing."""
        root = ET.fromstring(self.sample_xml)
        reading_order = self.parser._parse_reading_order(root)
        
        expected = {'region_1': 0, 'region_2': 1}
        self.assertEqual(reading_order, expected)
    
    def test_get_text_equiv(self):
        """Test text extraction."""
        root = ET.fromstring(self.sample_xml)
        region_elem = root.find('.//pc:TextRegion', self.parser.namespace)
        
        text = self.parser._get_text_equiv(region_elem)
        expected = "Test line 1\nTest line 2"
        
        self.assertEqual(text, expected)
    
    def test_parse_page_xml(self):
        """Test complete page XML parsing."""
        page_data = self.parser._parse_page_xml(self.sample_xml, "test_project")
        
        self.assertIsInstance(page_data, PageData)
        self.assertEqual(page_data.image_filename, "test.jpg")
        self.assertEqual(page_data.image_width, 1247)
        self.assertEqual(page_data.image_height, 1920)
        self.assertEqual(page_data.project_name, "test_project")
        self.assertEqual(len(page_data.regions), 1)
        
        region = page_data.regions[0]
        self.assertEqual(region.id, "region_1")
        self.assertEqual(region.type, "paragraph")
        self.assertEqual(len(region.text_lines), 2)
        
        line1 = region.text_lines[0]
        self.assertEqual(line1.id, "line_1")
        self.assertEqual(line1.text, "Test line 1")
        self.assertEqual(line1.reading_order, 0)
    
    def test_macos_metadata_file_filtering(self):
        """Test that macOS metadata files are properly filtered out."""
        # Test files that should be filtered out
        self.assertTrue(self.parser._is_macos_metadata_file("__MACOSX/file.xml"))
        self.assertTrue(self.parser._is_macos_metadata_file("._file.xml"))
        self.assertTrue(self.parser._is_macos_metadata_file("project/._page.xml"))
        self.assertTrue(self.parser._is_macos_metadata_file("project/.DS_Store"))
        
        # Test files that should NOT be filtered out
        self.assertFalse(self.parser._is_macos_metadata_file("project/page/file.xml"))
        self.assertFalse(self.parser._is_macos_metadata_file("project/page/valid.xml"))
        self.assertFalse(self.parser._is_macos_metadata_file("normal_file.xml"))


if __name__ == '__main__':
    unittest.main() 