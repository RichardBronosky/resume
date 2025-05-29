# resume-docx-generator

A Python tool for generating Microsoft Word (DOCX) resume files from YAML files that follow the JSON Resume schema.

## Features

- Generate professional DOCX resumes from YAML files
- Compatible with [JSON Resume schema](https://github.com/jsonresume/resume-schema)
- Clean and simple API
- Command-line interface
- PDF conversion support via LibreOffice (optional)
- Proper error handling and reporting

## Requirements

- Python 3.6 or higher
- LibreOffice (optional, for PDF conversion)

## Installation

```bash
# For production
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

## Usage

### As a Python Library

```python
from docx_generator import generate_resume

# Basic usage
success, message = generate_resume("resume.yaml", "output.docx")
if success:
    print(f"Resume created: {message}")
else:
    print(f"Error: {message}")

# With PDF conversion (requires LibreOffice)
success, message = generate_resume(
    "resume.yaml",
    "output.docx",
    convert_to_pdf=True
)
```

### Command Line Interface

```bash
# Basic usage
resume-docx resume.yaml

# Specify output file
resume-docx resume.yaml -o custom-resume.docx

# Generate PDF as well (requires LibreOffice)
resume-docx resume.yaml --pdf
```

### YAML Resume Format

Your resume should follow the JSON Resume schema format. Here's a basic example:

```yaml
basics:
  name: John Doe
  label: Programmer
  email: john@doe.com
  phone: (912) 555-4321
  url: https://johndoe.com
  summary: A summary of John Doe...
  location:
    city: San Francisco
    countryCode: US
    region: California

work:
  - company: Company
    position: Position
    website: https://company.com
    startDate: 2013-01-01
    endDate: 2014-01-01
    summary: Description...
    highlights:
      - Started the company
```

See the [JSON Resume Schema](https://github.com/jsonresume/resume-schema) for the full specification.

## Development

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Linux/Mac: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`
4. Install development dependencies: `pip install -r requirements-dev.txt`

## License

MIT License 