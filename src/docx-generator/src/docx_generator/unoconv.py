"""PDF conversion using local LibreOffice headless."""

import os
import subprocess
import logging
from typing import Tuple
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@contextmanager
def get_service():
    """Dummy context manager to maintain API compatibility with generator.py"""
    yield None

def docx_to_pdf(input_file: str) -> Tuple[bool, str]:
    """
    Convert a DOCX file to PDF using local LibreOffice.
    
    Args:
        input_file: Path to the input DOCX file
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        input_path = Path(input_file)
        if not input_path.exists():
            return False, f"Input file not found: {input_file}"
            
        output_dir = input_path.parent
        output_file = input_path.with_suffix('.pdf')
        
        # Check if libreoffice is available
        try:
            subprocess.run(['libreoffice', '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False, "LibreOffice is not installed or not in PATH. Run in: nix-shell -p libreoffice"

        logger.info(f"Converting {input_file} to PDF using local LibreOffice...")
        
        result = subprocess.run([
            'libreoffice', 
            '--headless', 
            '--convert-to', 'pdf', 
            str(input_path), 
            '--outdir', str(output_dir)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            return False, f"Conversion failed: {result.stderr}"
            
        if not output_file.exists():
            return False, "Conversion seemed to succeed, but PDF file was not created."
            
        return True, f"Successfully converted to {output_file}"
        
    except Exception as e:
        return False, f"Error converting to PDF: {str(e)}"
