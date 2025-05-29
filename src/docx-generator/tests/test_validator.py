"""
Tests for the docx_generator.validator module.
"""

import pytest
import yaml
from docx_generator.validator import load_yaml, load_schema

def test_load_schema():
    """Test that the JSON Resume schema can be loaded."""
    schema = load_schema()
    assert isinstance(schema, dict)
    assert "properties" in schema
    assert "basics" in schema["properties"]

def test_load_yaml(tmp_path):
    """Test loading and validating a YAML file."""
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
    
    data = load_yaml(str(yaml_path))
    assert isinstance(data, dict)
    assert "basics" in data
    assert data["basics"]["name"] == "John Doe"

def test_load_yaml_missing_schema(tmp_path):
    """Test loading a YAML file without schema reference."""
    yaml_path = tmp_path / "no_schema.yaml"
    yaml_path.write_text("basics:\n  name: John Doe")
    
    with pytest.raises(ValueError) as exc_info:
        load_yaml(str(yaml_path))
    assert "No document with $schema field found" in str(exc_info.value)

def test_load_yaml_invalid_yaml(tmp_path):
    """Test loading an invalid YAML file."""
    yaml_path = tmp_path / "invalid.yaml"
    yaml_path.write_text("invalid: }")
    
    with pytest.raises(yaml.YAMLError) as exc_info:
        load_yaml(str(yaml_path))
    assert "Error parsing YAML file" in str(exc_info.value) 