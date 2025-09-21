import json
from pathlib import Path
import pytest

from quadre.validator import Document


def test_examples():
    """Test that all JSON files in examples directory can be successfully validated."""
    # Get the examples directory path
    test_dir = Path(__file__).parent
    project_root = test_dir.parent
    examples_dir = project_root / "examples"

    # Ensure examples directory exists
    if not examples_dir.exists():
        pytest.skip(f"Examples directory not found: {examples_dir}")

    # Find all JSON files
    json_files = list(examples_dir.glob("*.json"))

    if not json_files:
        pytest.skip("No JSON files found in examples directory")

    # Test each JSON file
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Validate JSON syntax
            json.loads(content)

            # Validate against Document schema
            doc = Document.model_validate_json(content)
            assert doc is not None, f"Document validation returned None for {json_file.name}"

        except Exception as e:
            pytest.fail(f"Failed to validate {json_file.name}: {e}")
