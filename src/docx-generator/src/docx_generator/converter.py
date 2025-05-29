"""
Core functionality for converting DOCX files to PDF using LibreOffice.
"""

import pty
import subprocess
import os
from typing import Optional, Tuple

def docx_to_pdf(input_file: str, output_file: Optional[str] = None) -> Tuple[bool, str]:
    """
    Convert a DOCX file to PDF using LibreOffice in headless mode.
    
    Args:
        input_file (str): Path to the input DOCX file
        output_file (Optional[str]): Path to the output PDF file. If not provided,
                                   will use the same name as input with .pdf extension
    
    Returns:
        Tuple[bool, str]: A tuple containing:
            - bool: True if conversion was successful, False otherwise
            - str: Output message or error description
    
    Example:
        >>> success, message = docx_to_pdf("document.docx")
        >>> if success:
        ...     print(f"PDF created: {message}")
        ... else:
        ...     print(f"Error: {message}")
    """
    if not os.path.exists(input_file):
        return False, f"Input file '{input_file}' not found"
    
    if not input_file.lower().endswith('.docx'):
        return False, f"Input file '{input_file}' is not a .docx file"
    
    # If no output file specified, use input filename with .pdf extension
    if output_file is None:
        output_file = os.path.splitext(input_file)[0] + '.pdf'
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    def run_with_pty(cmd):
        devnull = open(os.devnull, 'r+b', 0)
        master, slave = pty.openpty()
        process = subprocess.Popen(
            cmd,
            stdin=devnull,
            stdout=slave,
            stderr=slave,
            close_fds=True,
            preexec_fn=os.setsid
        )
        os.close(slave)
        
        output = b""
        while True:
            try:
                data = os.read(master, 1024)
                if not data:
                    break
                output += data
            except OSError:
                break
        
        process.wait()
        os.close(master)
        devnull.close()
        return process.returncode, output.decode('utf-8', errors='replace')
    
    # Run LibreOffice conversion
    return_code, output = run_with_pty([
        'libreoffice',
        '--headless',
        '--convert-to', 'pdf',
        '--outdir', os.path.dirname(output_file) or '.',
        input_file
    ])
    
    if return_code != 0:
        return False, f"LibreOffice conversion failed with return code {return_code}: {output}"
    
    if not os.path.exists(output_file):
        return False, "PDF file was not created"
    
    return True, f"Successfully converted '{input_file}' to '{output_file}'" 