"""
Tests for the docx_generator.generator module.
"""

import os
import pytest
from docx import Document
from docx_generator.generator import generate_resume

@pytest.fixture
def yaml_file(tmp_path):
    """Create a temporary YAML file with valid resume data."""
    yaml_path = tmp_path / "test_resume.yaml"
    yaml_path.write_text("""
$schema: https://raw.githubusercontent.com/jsonresume/resume-schema/v1.0.0/schema.json
basics:
  name: John Doe
  email: john@example.com
  phone: (555) 555-5555
  summary: A test summary
work:
  - company: Test Company
    position: Software Engineer
    startDate: "2020-01"
    endDate: "Present"
    summary: Work summary
    highlights:
      - Achievement 1
      - Achievement 2
education:
  - institution: Test University
    area: Computer Science
    studyType: Bachelor
    startDate: "2016"
    endDate: "2020"
skills:
  - name: Programming
    keywords:
      - Python
      - JavaScript
""")
    return str(yaml_path)

@pytest.fixture
def output_file(tmp_path):
    """Create a temporary output file path."""
    return str(tmp_path / "output.docx")

def test_generate_resume(yaml_file, output_file):
    """Test generating a DOCX resume from YAML."""
    success, message = generate_resume(yaml_file, output_file)
    assert success, message
    assert os.path.exists(output_file)
    
    # Verify the generated document
    doc = Document(output_file)
    paragraphs = [p.text for p in doc.paragraphs]
    
    # Check if basic information is present
    assert any("John Doe" in p for p in paragraphs)
    assert any("john@example.com" in p for p in paragraphs)
    assert any("Test Company" in p for p in paragraphs)
    assert any("Software Engineer" in p for p in paragraphs) 