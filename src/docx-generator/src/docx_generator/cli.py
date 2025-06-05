"""
Command-line interface for resume-docx-generator.
"""

import sys
import os
import argparse
from .generator import generate_resume

def add_ats_suffix(filename: str) -> str:
    """Add .ats before the final extension of a filename."""
    base, ext = os.path.splitext(filename)
    return f"{base}.ats{ext}"

def main():
    """Entry point for the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Generate Microsoft Word resumes from YAML files following the JSON Resume schema"
    )
    parser.add_argument(
        "yaml_file",
        help="Path to the input YAML resume file"
    )
    parser.add_argument(
        "-o", "--output",
        help="Path to the output DOCX file (default: based on input filename)",
        default=None
    )
    parser.add_argument(
        "--pdf",
        help="Also generate a PDF version (requires LibreOffice)",
        action="store_true"
    )
    parser.add_argument(
        "--ats",
        help="Format work experience entries in ATS-friendly format",
        action="store_true"
    )
    
    args = parser.parse_args()
    
    # Handle output filename
    if args.output is None:
        # Default filename based on input
        base = args.yaml_file.rsplit(".", 1)[0]
        output_file = f"{base}.docx"
    else:
        # Use provided output name
        output_file = args.output
    
    # Add .ats suffix if ATS format is requested
    if args.ats:
        output_file = add_ats_suffix(output_file)
    
    success, message, page_count = generate_resume(
        args.yaml_file,
        output_file,
        convert_to_pdf=args.pdf,
        ats_format=args.ats
    )
    
    # If PDF was generated, also show its name in the message
    if success and args.pdf:
        pdf_file = os.path.splitext(output_file)[0] + ".pdf"
        message = message.replace(" and PDF version", f" and PDF version ({pdf_file})")
    
    print(message)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 