"""
resume-docx-generator - Generate Microsoft Word resumes from YAML files following the JSON Resume schema
"""

from .generator import generate_resume
from .converter import docx_to_pdf

__version__ = "0.1.0"
__all__ = ["generate_resume", "docx_to_pdf"] 