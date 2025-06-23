"""
transkribus-hf: Convert Transkribus ZIP files to HuggingFace datasets
"""

from .converter import TranskribusConverter
from .parser import TranskribusParser
from .exporters import (
    RawXMLExporter,
    TextExporter,
    RegionExporter,
    LineExporter,
    WindowExporter,
)

__version__ = "0.1.0"
__author__ = "wjbmattingly"

__all__ = [
    "TranskribusConverter",
    "TranskribusParser",
    "RawXMLExporter",
    "TextExporter", 
    "RegionExporter",
    "LineExporter",
    "WindowExporter",
] 