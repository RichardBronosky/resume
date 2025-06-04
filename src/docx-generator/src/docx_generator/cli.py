"""
Command-line interface for resume-docx-generator.
"""

import sys
import argparse
from .generator import generate_resume

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
    
    # If no output file specified, use input filename with .docx extension
    if args.output is None:
        args.output = args.yaml_file.rsplit(".", 1)[0] + ".docx"
    
    success, message, page_count = generate_resume(
        args.yaml_file,
        args.output,
        convert_to_pdf=args.pdf,
        ats_format=args.ats
    )
    print(message)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 