"""
Validation functionality for JSON Resume YAML files.
"""

import os
import yaml
import json
import jsonschema
from datetime import datetime
from typing import Dict, Any, List
from copy import deepcopy

def load_schema() -> Dict[str, Any]:
    """Load the JSON Resume schema."""
    schema_path = os.path.join(os.path.dirname(__file__), "schema", "schema.json")
    with open(schema_path) as f:
        return json.load(f)

def _prepare_dates_for_validation(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create a copy of items with 'Present' dates converted to a format suitable for validation.
    Does not modify the original data.
    
    Args:
        items: List of dictionaries containing date information
    Returns:
        A copy of the items with dates prepared for validation
    """
    if not isinstance(items, list):
        return items
        
    items_copy = deepcopy(items)
    for item in items_copy:
        if isinstance(item, dict) and "endDate" in item:
            if str(item["endDate"]).lower() == "present":
                item["endDate"] = datetime.now().strftime("%Y")
    return items_copy

def validate_resume_data(data: Dict[str, Any]) -> None:
    """
    Validate resume data against the schema.
    Creates a temporary copy for validation, leaving original data unchanged.
    
    Args:
        data: The resume data to validate
    """
    if not isinstance(data, dict):
        return
        
    # Create a copy for validation
    validation_data = deepcopy(data)
    
    # Prepare dates in the copy
    for section in ["work", "education"]:
        if section in validation_data:
            validation_data[section] = _prepare_dates_for_validation(validation_data[section])
    
    # Validate the prepared copy
    schema = load_schema()
    jsonschema.validate(validation_data, schema)

def load_yaml(yaml_file: str) -> Dict[str, Any]:
    """
    Load and validate a YAML resume file against the JSON Resume schema.
    
    Args:
        yaml_file: Path to the YAML file to load and validate
        
    Returns:
        Dict containing the original, unmodified resume data
        
    Raises:
        ValueError: If no document with $schema field is found
        yaml.YAMLError: If YAML parsing fails
        jsonschema.exceptions.ValidationError: If schema validation fails
    """
    try:
        with open(yaml_file) as f:
            # Load all documents from the YAML file
            documents = list(yaml.safe_load_all(f))
            
            # Find the document that has the $schema field
            resume_data = None
            for doc in documents:
                if isinstance(doc, dict) and "$schema" in doc:
                    resume_data = doc
                    break
            
            if resume_data is None:
                raise ValueError("No document with $schema field found in YAML file")
        
        # Validate the data without modifying it
        validate_resume_data(resume_data)
        
        # Return the original, unmodified data
        return resume_data
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file: {str(e)}") 